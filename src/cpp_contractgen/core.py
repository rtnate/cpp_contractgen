from .config import Config
from .policy import Policy
from dataclasses import dataclass, field
from pathlib import Path
import logging
from typing import Optional
from .policy import OnBuildPolicy, GenerationMode
from .user_confirm import ConfirmManager
from .parser import parse_contract
from .generator import generate_contract
from .dummy_header import generate_header
from cpp_contractgen import ExitCode
from .files import (
    PathLike,
    find_file, 
    find_files, 
    file_exists,
    hash_file,
    extract_hash_from_text, 
    write_file,
    read_file_text,
    resolve_file 
)

CONTRACT_EXT = ".hpp.contract"

@dataclass
class Job:
    input_file: Path
    output_file: Path
    action: str
    policy: Policy


def create_policy_from_args_and_config(args, config: Config) -> Policy:
    return Policy.from_args_and_config(args, config)

def discover_files_emit_header(policy: Policy) -> list[Path]:
    logging.debug("Emit-header mode: no contract files to discover")
    return []

def discover_files_single_file_mode(policy: Policy) -> list[Path]:
    # Single file mode
    """
    Discover input contract files based on the policy.
    Returns a list of Paths to .hpp.contract files.
    """
    logging.debug("Generation mode: single - Policy contract: %s" %(policy.in_file))
    if not policy.in_file:
        logging.error("Single-file mode requires --contract <file>")
        return []
    in_file = find_file(policy.in_file)
    if in_file:
        return [in_file]
    else:
        return []
    
def discover_files_batch_mode(policy: Policy) -> list[Path]:
    # Batch search
    logging.debug("Generation mode: batch - Policy search: %s" %(policy.search_dirs))
    search_dirs = policy.search_dirs or []
    files = find_files(search_dirs)
    logging.info("Total contracts discovered: %d", len(files))
    return sorted(files)

def discover_files(policy: Policy) -> list[Path]:
    """
    Discover contract files based on the given Policy.
    
    Returns:
        List of Paths to .hpp.contract files.
    """
    files: list[Path] = []
    if policy.generation_mode == GenerationMode.EMIT_HEADER:
        return discover_files_emit_header(policy)
    elif policy.generation_mode == GenerationMode.SINGLE_FILE: 
        return discover_files_single_file_mode(policy)
    else:
        return discover_files_batch_mode(policy)



def determine_job_action(on_build: OnBuildPolicy, out_file: Optional[PathLike]) -> str:
    if on_build == OnBuildPolicy.NONE:
        return "skip"
    elif on_build == OnBuildPolicy.GENERATE_MISSING:
        if file_exists(out_file):
             return "skip"
        else:
             return "generate"
    elif on_build == OnBuildPolicy.FORCE:
         return "generate"
    elif on_build == OnBuildPolicy.OVERWRITE:
         return "generate"
    elif on_build == OnBuildPolicy.CHECK_DIFF:
         return "check"
    else:
        return "generate"  # safe fallback


def build_standard_job(policy: Policy, in_file: PathLike) -> Job:
    file_policy = policy.get_policy_for_file(in_file)
    out_file = file_policy.resolve_output_file(in_file)
    action = determine_job_action(file_policy.on_build, out_file)

    return Job(
        input_file= resolve_file(in_file),
        output_file= resolve_file(out_file),
        action=action,
        policy=file_policy
    )

def build_emit_header_job(policy: Policy) -> Job:
    if not policy.emit_header:
        logging.error("Emit-header mode requires an emit_header path")
        return []

    return Job(
        input_file= None,   # no input file, synthetic job
        output_file= resolve_file(policy.emit_header),
        action="emit_header",
        policy=policy,
    )

def build_jobs(policy: Policy, files: list[Path]) -> list[Job]:
    """
    Build a list of Job objects from discovered files and policy.
    """
    jobs: list[Job] = []

    if policy.generation_mode == GenerationMode.EMIT_HEADER:
        jobs.append(build_emit_header_job(policy))
    else:
        for in_file in files:
            job = build_standard_job(policy, in_file)
            jobs.append(job)
            logging.debug(
                "Prepared job: %s -> %s (action=%s)",
                job.input_file, job.output_file, job.action
            )
    logging.info("Built %d jobs", len(jobs))
    return jobs


def execute_job(job: Job, userConfirm: "ConfirmManager|None" = None) -> int:
    confirm = userConfirm if userConfirm else ConfirmManager.none()

    in_file = resolve_file(job.input_file)
    out_file = resolve_file(job.output_file)
    policy = job.policy

    try:
        if job.action == 'emit_header':
            header = generate_header(policy)
            write_file(out_file, header)
            return 0
        else:
            if not in_file:
                raise FileNotFoundError("Error: In File must be supplied except"
                                        " in 'emit-header' mode")
        # Hash the contract file
        contract_hash = hash_file(in_file)
        # Parse
        contract = parse_contract(in_file)

        # Generate new text (always)
        new_text = generate_contract(contract, contract_hash, policy.embed_contract)

        if file_exists(out_file):
            logging.debug("Output file already %s already exists" %(out_file))
            old_text = read_file_text(out_file)
            old_hash = extract_hash_from_text(old_text)

            if policy.on_build == OnBuildPolicy.CHECK_DIFF:
                if old_hash != contract_hash:
                    logging.warning("Contract mismatch in %s", out_file)
                    return 1
                else: 
                   #TODO: Log matching hash - info logs that it matches - debug with hash details
                    return 0

            elif policy.on_build == OnBuildPolicy.OVERWRITE:
                if confirm.confirm_overwrite(out_file, prefix="Contract"):
                    write_file(out_file, new_text)
                    logging.info("Overwrote %s", out_file)
                    return 0
                else:
                    #TODO: handle overwrite non-confirm (log probably)
                    return 0

            elif policy.on_build == OnBuildPolicy.GENERATE_MISSING:
                logging.debug("File exists, skipping: %s", out_file)
                return 0

            else:  # DIFF or other
                if old_hash != contract_hash:
                    logging.warning("Difference in %s", out_file)
                    print(f"Old hash: {old_hash or 'none'}")
                    print(f"New hash: {contract_hash}")
                    return 1
                return 0

        else: 
            # File missing
            generated = generate_contract(contract, contract_hash, policy.embed_contract)
            if policy.on_build in (
                OnBuildPolicy.FORCE,
                OnBuildPolicy.GENERATE_MISSING,
                OnBuildPolicy.OVERWRITE,
            ) or policy.use_std_out:
                write_file(out_file, generated)
                logging.info("Generated %s", out_file)
                return 0
            else:
                logging.info("Generated Contract File Does Not Exist: %s" %(out_file))
                return 1

    except Exception as e:
        logging.critical("Job failed for %s: %s", in_file, e, exc_info=True)
        raise e

def build_and_execute_policy(policy: Policy, userConfirm: Optional[ConfirmManager] = None):
    files = discover_files(policy)
    jobs = build_jobs(policy, files)
    diff_count_result = 0
    for job in jobs:
            result = execute_job(job, userConfirm)
            diff_count_result += result
    if diff_count_result > 0:
        #TODO: output results 
        return 1
    else:
        return 0
    