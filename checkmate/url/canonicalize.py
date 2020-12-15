"""An implementation of Google Web Risk URL canonicalization.

As defined here: https://cloud.google.com/web-risk/docs/urls-hashing#canonicalization
"""

import os.path
import re
from urllib.parse import unquote, urlparse, urlunparse

from netaddr import AddrFormatError, IPAddress


class CanonicalURL:
    """Implementation of Google Web Risk URL canonicalization."""

    @classmethod
    def canonicalize(cls, url):
        """Convert a URL to a canonical form for comparison.

        This may "invent" a scheme as necessary.

        :param url: URL to normalise
        :return: A normalised version of the URL
        """
        parts = cls.canonical_split(url)
        clean_url = urlunparse(parts)

        # Get around the fact that URL parse strips off the '?' if the query
        # string is empty
        if url.endswith("?") and not clean_url.endswith("?"):
            clean_url += "?"

        return clean_url

    @classmethod
    def canonical_split(cls, url):
        """Split a URL into canonical parts.

        Note the fragment is always `None`. It is only returned for
        compatibility with the arguments of `urllib.parse.urlunparse()`

        :return: Tuple of (scheme, netloc, path, params, query, fragment)
        """
        scheme, netloc, path, params, query = cls._pre_process_url(url)

        netloc = cls._canonicalize_host(netloc)
        path = cls._canonicalize_path(path)

        # In the URL, percent-escape all characters that are <= ASCII 32, >=
        # 127, #, or %. The escapes should use uppercase hex characters.
        netloc = cls._partial_quote(netloc)
        path = cls._partial_quote(path)
        query = cls._partial_quote(query)

        return scheme, netloc, path, params, query, None

    BANNED_CHARS = re.compile("[\x09\x0d\x0a]")
    SCHEME_PREFIX = re.compile(r"^([A-z]+):/+")

    @classmethod
    def _pre_process_url(cls, url):
        # https://cloud.google.com/web-risk/docs/urls-hashing#canonicalization

        clean_url = url.strip()

        # First, remove tab (0x09), CR (0x0d), and LF (0x0a) characters from
        # the URL. Do not remove escape sequences for these characters,
        # like %0a.

        clean_url = cls.BANNED_CHARS.sub("", clean_url)

        # This is our own tweak, but if we have URLs like:
        # http:/example.com or http:///example.com Chrome will go there so
        # lets convert them to always have two slashes

        clean_url = cls.SCHEME_PREFIX.sub("\\1://", clean_url)

        # Second, if the URL ends in a fragment, remove the fragment. For
        # example, shorten http://google.com/#frag to http://google.com/.

        scheme, netloc, path, params, query, _fragment = urlparse(clean_url)

        if not scheme:
            if not netloc:
                # Without a scheme urlparse often assumes the domain is the
                # path. To prevent this add a fake scheme and try again
                return cls._pre_process_url("http://" + url)

            # Looks like we have a domain, but no scheme, so make one up
            scheme = "http"

        # Third, repeatedly remove percent-escapes from the URL until it has
        # no more percent-escapes.

        netloc = cls._repeated_unquote(netloc)
        path = cls._repeated_unquote(path)
        query = cls._repeated_unquote(query)

        return scheme, netloc, path, params, query

    CONSECUTIVE_DOTS = re.compile(r"\.\.+")
    PORT = re.compile(r":\d+$")

    @classmethod
    def _canonicalize_host(cls, hostname):
        # https://cloud.google.com/web-risk/docs/urls-hashing#to_canonicalize_the_hostname

        # If the URL uses an internationalized domain name (IDN), the client
        # should convert the URL to the ASCII Punycode representation.
        try:
            # https://docs.python.org/3/library/codecs.html#module-encodings.idna
            hostname = hostname.encode("idna").decode("ascii")
        except UnicodeError:
            # Oh well
            pass

        # 1. Remove all leading and trailing dots.
        hostname = hostname.strip(".")

        # 2. Replace consecutive dots with a single dot.
        hostname = cls.CONSECUTIVE_DOTS.sub(".", hostname)

        # Not in the text, but in the test cases
        hostname = cls.PORT.sub("", hostname)

        # 3. If the hostname can be parsed as an IP address, normalize it to 4
        # dot-separated decimal values. The client should handle any legal
        # IP-address encoding, including octal, hex, and fewer than
        # four components.
        ip_address = cls._decode_ip(hostname)
        if ip_address:
            hostname = ip_address

        # 4. Lowercase the whole string.
        hostname = hostname.lower()

        return hostname

    CONSECUTIVE_SLASHES = re.compile("//+")

    @classmethod
    def _canonicalize_path(cls, path):
        # https://cloud.google.com/web-risk/docs/urls-hashing#to_canonicalize_the_path

        # 1. Resolve the sequences /../ and /./ in the path by replacing
        # /./ with /, and removing /../ along with the preceding path
        # component.
        if path:
            path = os.path.normpath(path) + ("/" if path.endswith("/") else "")

        # 2. Replace runs of consecutive slashes with a single slash character.
        path = cls.CONSECUTIVE_SLASHES.sub("/", path)

        return path or "/"

    HEX_DOT_IP = re.compile(r"^[0-f]+\.[0-f]+\.[0-f]+\.[0-f]+$", re.IGNORECASE)
    BINARY_DOT_IP = re.compile(r"^[01]+\.[01]+\.[01]+\.[01]+$", re.IGNORECASE)

    @classmethod
    def _decode_ip(cls, hostname):
        """Try and spot hostnames that are really encoded IP addresses."""
        if cls.HEX_DOT_IP.match(hostname):
            decoded = cls._decode_ip("0x" + hostname.replace(".", ""))

            if decoded:
                return decoded

        if cls.BINARY_DOT_IP.match(hostname):
            parts = [str(int(part, 2)) for part in hostname.split(".")]
            return ".".join(parts)

        try:
            return str(IPAddress(hostname))
        except AddrFormatError:
            return None

    @classmethod
    def _repeated_unquote(cls, string):
        decoded = unquote(string)

        # Keep decoding until the string stops changing
        while decoded != string:
            string = decoded
            decoded = unquote(string)

        return decoded

    @classmethod
    def _partial_quote(cls, string):
        parts = []
        for char in string:
            char_code = ord(char)

            # In the URL, percent-escape all characters that are <= ASCII 32,
            # >= 127, #, or %. The escapes should use uppercase hex characters.
            if char_code <= 32 or char_code >= 127 or char in "#%":
                parts.append("%{:02X}".format(char_code))
            else:
                parts.append(char)

        final = "".join(parts)
        return final
