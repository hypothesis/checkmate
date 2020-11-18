import os.path
import re
from urllib.parse import unquote, urlparse, urlunparse

from netaddr import AddrFormatError, IPAddress


class CanonicalURL:
    @classmethod
    def canonicalise(cls, url):
        scheme, netloc, path, params, query = cls.pre_process_url(url)

        netloc = cls.canonicalize_host(netloc)
        path = cls.canonicalize_path(path)

        # In the URL, percent-escape all characters that are <= ASCII 32, >=
        # 127, #, or %. The escapes should use uppercase hex characters.
        netloc = cls.partial_quote(netloc)
        path = cls.partial_quote(path)

        clean_url = urlunparse([scheme, netloc, path, params, query, None])

        # Get around the fact that URL parse strips off the '?' if the query
        # string is empty
        if url.endswith("?") and not clean_url.endswith("?"):
            clean_url += "?"

        return clean_url

    BANNED_CHARS = re.compile("[\x09\x0d\x0a]")

    @classmethod
    def pre_process_url(cls, url):
        # https://cloud.google.com/web-risk/docs/urls-hashing#canonicalization

        clean_url = url.strip()

        # First, remove tab (0x09), CR (0x0d), and LF (0x0a) characters from
        # the URL. Do not remove escape sequences for these characters,
        # like %0a.

        clean_url = cls.BANNED_CHARS.sub("", clean_url)

        # Second, if the URL ends in a fragment, remove the fragment. For
        # example, shorten http://google.com/#frag to http://google.com/.

        scheme, netloc, path, params, query, _fragment = urlparse(clean_url)

        if not scheme and not netloc:
            # Without a scheme urlparse goes totally crazy, so add a default
            # and try again
            return cls.pre_process_url("http://" + url)

        # Third, repeatedly remove percent-escapes from the URL until it has
        # no more percent-escapes.

        netloc = cls.repeated_unquote(netloc)
        path = cls.repeated_unquote(path)

        return scheme, netloc, path, params, query

    CONSECUTIVE_DOTS = re.compile(r"\.\.+")
    PORT = re.compile(r":\d+$")

    @classmethod
    def canonicalize_host(cls, hostname):
        # https://cloud.google.com/web-risk/docs/urls-hashing#to_canonicalize_the_hostname

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
        ip_address = cls.decode_ip(hostname)
        if ip_address:
            hostname = ip_address

        # 4. Lowercase the whole string.
        hostname = hostname.lower()

        return hostname

    CONSECUTIVE_SLASHES = re.compile("//+")

    @classmethod
    def canonicalize_path(cls, path):
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
    def decode_ip(cls, hostname):
        if cls.HEX_DOT_IP.match(hostname):
            decoded = cls.decode_ip("0x" + hostname.replace(".", ""))

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
    def repeated_unquote(cls, string):
        next = unquote(string)
        while next != string:
            string = next
            next = unquote(string)

        return next

    @classmethod
    def partial_quote(cls, string):
        parts = []
        for char in string:
            char_code = ord(char)

            # In the URL, percent-escape all characters that are <= ASCII 32,
            # >= 127, #, or %. The escapes should use uppercase hex characters.
            if char_code <= 32 or char_code >= 127 or char in "#%":
                # TODO! Use a format string here
                encoding = hex(char_code)[2:].upper()
                if len(encoding) == 1:
                    encoding = "0" + encoding

                parts.append("%" + encoding)
            else:
                parts.append(char)

        final = "".join(parts)
        return final
