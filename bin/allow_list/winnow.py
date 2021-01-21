def winnow(domain_set):
    """Remove any domains which are sub-domains of another."""

    winnowed = _winnow(domain_set)
    while winnowed:
        winnowed = _winnow(domain_set)


def _winnow(domain_set):
    winnowed = set()

    for domain in domain_set:
        if domain.endswith("hypothes.is"):
            continue

        # Find out how many labels there are in the root domain by counting
        # dots
        domain_depth = domain.count(".") + 1
        root_depth = domain.root_domain.count(".") + 1

        for suffix in domain.suffixes(min_depth=root_depth, max_depth=domain_depth - 1):
            if suffix in domain_set:
                winnowed.add(domain)

    domain_set -= winnowed

    return winnowed
