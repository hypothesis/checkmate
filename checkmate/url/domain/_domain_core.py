import re
from functools import lru_cache


class DomainCore(str):
    """Represent a domain string with metadata.

    This metadata is only that which can be derived from the string itself
    without any lookup data.
    """

    def __new__(cls, domain, **kwargs):
        return super().__new__(cls, cls._normalize(domain), **kwargs)

    IP_V4 = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    PORT = re.compile(r":\d*$")
    USER_PASS = re.compile(r"^.*@")

    # https://www.geeksforgeeks.org/how-to-validate-a-domain-name-using-regular-expression/
    VALID_PQDN = re.compile(
        r"^((?!-)[a-z0-9-]{1,63}(?<!-)\.)*(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE
    )

    @property
    @lru_cache(1)
    def is_valid(self):
        """Get whether the domain is valid at all.

        A valid domain name consists of one or more valid domain labels joined
        with dots. With various caveats. This does not imply the name is
        public or can be resolved.
        """
        if len(self) > 253:
            return False

        return bool(self.VALID_PQDN.match(self))

    @property
    @lru_cache(1)
    def is_ip_v4(self):
        """Get whether the domain is an IP V4 address."""

        if not self.IP_V4.match(self):
            return False

        # We could do this all in the regex, but it would be hideous
        for digit in self.labels:
            if int(digit) > 255:
                return False

        return True

    @property
    @lru_cache(1)
    def is_private_ip_v4(self):
        """Get whether the domain is a private IP V4 address."""

        if not self.is_ip_v4:
            return False

        digits = [int(digit) for digit in self.labels]

        if digits == [0, 0, 0, 0]:
            return True

        # 127.  0.0.0 – 127.255.255.255     127.0.0.0 /8
        # 10.  0.0.0 –  10.255.255.255      10.0.0.0 /8
        if digits[0] in (127, 10):
            return True

        # 172. 16.0.0 – 172. 31.255.255    172.16.0.0 /12
        if digits[0] == 172 and 16 <= digits[1] <= 31:
            return True

        # 192.168.0.0 – 192.168.255.255   192.168.0.0 /16
        return digits[0] == 192 and digits[1] == 168

    @property
    @lru_cache(1)
    def labels(self):
        """Get a list of the domain labels.

        Domain labels are the parts separated by dots. In the case of IP
        addresses this will return the strings of the digits.
        """
        return self.split(".")

    def suffix(self, depth):
        """Get a suffix of this domain up to a specified depth.

        For example if your domain is:

            a.b.c.com

        Then the following will be returned for various depths:

            1: com
            2: c.com
            3: b.c.com
            4: a.b.c.com

        :param depth: Number of labels to include in suffix.
        :return: String suffix or None for IP addresses
        """
        if self.is_ip_v4:
            return None

        if depth >= len(self.labels):
            return str(self)

        return ".".join(self.labels[len(self.labels) - depth :])

    def suffixes(self, min_depth=None, max_depth=None, include_domain=True):
        """Get a list of suffixes for the domain.

        A convenient alternative to `suffix` when you need multiple suffixes.

        No suffixes are returned for IP addresses.

        :param min_depth: Minimum number of labels to include
        :param max_depth: Maximum number of labels to include
        :param include_domain: Include the domain itself in the list
        :return: A generator of suffixes, shortest first
        """
        if self.is_ip_v4:
            return

        suffix = None
        for pos, part in enumerate(reversed(self.labels)):
            if max_depth is not None and pos >= max_depth:
                break

            if suffix is None:
                suffix = part
            else:
                suffix = f"{part}.{suffix}"

            if not include_domain and pos == len(self.labels) - 1:
                break

            if not min_depth or pos >= min_depth - 1:
                yield suffix

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    @classmethod
    def _normalize(cls, domain):
        domain = domain.strip()
        domain = cls.PORT.sub("", domain)
        domain = cls.USER_PASS.sub("", domain)

        return domain
