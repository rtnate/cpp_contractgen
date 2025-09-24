from pathlib import Path
from .policy import Policy
import sys
DUMMY_HEADER = """\
// cpp_contractgen dummy header
#pragma once

#ifndef CPP_CONTRACTGEN_DEFINED
#define CPP_CONTRACTGEN_DEFINED

#define define_contract struct

#endif // CPP_CONTRACTGEN_DEFINED
"""

def generate_header(policy: Policy):
    rendered = DUMMY_HEADER
    return rendered
