"""A script which builds a reverse suffix tree to spot common suffixes.

This attempts to spot odd branching behavior indicating many sub domains are
actually variations of one super domain.
"""

from bin.allow_list.file_tools import load_text, save_text
from bin.allow_list.winnow import winnow
from checkmate.url import Domain


class SuffixNode:
    def __init__(self, part, parent=None):
        self.part = part
        self.count = 0
        self.parent = parent

        if parent is None:
            self.depth = 0
        else:
            self.depth = parent.depth + 1

        self.children = {}

    def add_child(self, part):
        if part not in self.children:
            self.children[part] = SuffixNode(part, parent=self)

        self.count += 1

        return self.children[part]

    def add_children(self, parts):
        target = self
        for part in parts:
            target = target.add_child(part)

        target.count += 1

    def ancestors(self):
        target = self

        while target.parent is not None:
            yield target
            target = target.parent

    def leaves(self):
        if not self.children:
            yield self

        for child in self.children.values():
            yield from child.leaves()

    def as_str(self):
        return ".".join(node.part for node in self.ancestors())

    def __repr__(self):
        return f"<Suffix {self.as_str()}:{self.count}>"

    def as_dict(self):
        return [
            self.count,
            {key: value.as_dict() for key, value in self.children.items()},
        ]


# domain_names = {"www.google.com", "foo.google.com"}


def reduce_tree(tree, truncate_callback=lambda tree: None):
    if not tree.children:
        yield tree
        return

    truncate = False

    if tree.depth > 1:
        diffs = [tree.count - child.count for child in tree.children.values()]
        max_diff = max(diffs)

        if tree.depth < 3 and max_diff > 50:
            # High level domains with big drop offs
            truncate = False
        elif max_diff == 0:
            # Things which only ever appear after each other
            truncate = False
        elif max_diff > 2:
            # Some variation
            truncate = True

        if truncate:
            truncate_callback(tree)

    if truncate:
        yield tree
    else:
        for child in tree.children.values():
            yield from reduce_tree(child, truncate_callback)


def build_suffix_tree(domains):
    tree = SuffixNode(None)

    for domain in domains:
        if domain.is_ip_v4:
            continue

        # The root nodes of the tree should be an icann suffix + one label
        sub_domains, root_domain = domain.split_domain(icann_only=True)
        if not sub_domains:
            tree.add_children([domain])
            continue

        parts = [root_domain] + list(reversed(sub_domains))

        tree.add_children(parts)

    return tree


def identify_suffixes(tree):
    # Truncate the tree where we spot oddities
    suffixes = set()

    def on_truncate(tree):
        print("Truncating tree at", tree)
        suffixes.add(tree.as_str())

    for _ in reduce_tree(tree, on_truncate):
        ...

    return suffixes


def knowledge_based_suffixes(domains):
    # These are all things that tend to indicate educational institution
    # proxies
    KNOWN_SUFFIX_STARTERS = {
        "ezp",
        "ezproxy",
        "lib",
        "libproxy",
        "libproxy1",
        "libproxy2",
        "libproxy3",
        "libraries",
        "library",
        "libraryproxy",
        "libweb",
        "proxy",
        "bib",
        "bibl",
    }

    for domain in domains:
        sub_domains, root_domain = domain.split_domain()

        for pos, label in enumerate(sub_domains):
            if label in KNOWN_SUFFIX_STARTERS:
                new_domain = ".".join(sub_domains[pos:]) + "." + root_domain
                yield new_domain


def remove_known_bad(suffixes):
    return {suffix for suffix in suffixes if not suffix.endswith("amazonaws.com")}


if __name__ == "__main__":
    domains = [Domain(domain) for domain in load_text("process/02_domains.txt")]

    knowledge_suffixes = set(knowledge_based_suffixes(domains))

    tree = build_suffix_tree(domains)
    auto_suffixes = set(identify_suffixes(tree))

    print(f"{len(knowledge_suffixes)} knowledge based suffixes")
    print(f"{len(auto_suffixes)} auto suffixes")

    suffixes = {Domain(suffix) for suffix in auto_suffixes | knowledge_suffixes}
    suffixes = remove_known_bad(suffixes)

    print(f"{len(suffixes)} pre-winnow")
    winnow(suffixes)
    print(f"{len(suffixes)} final")

    save_text("process/03_auto_suffixes.txt", sorted(suffixes))
