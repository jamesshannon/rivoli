Validator function signatures specify the types that the method _could_ accept
and will raise an exception if incompatible at runtime. For example, a
validator that checks for a minimum numeric value would accept str, float, and
int, with the assumption that the string can be converted and will try at
runtime
