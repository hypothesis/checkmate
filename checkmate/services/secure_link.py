"""Create and check secure links."""

from hashlib import sha256


class SecureLinkService:
    """A class for generating secure links to our own routes."""

    TOKEN_ARG = "sec"
    VERSION_ARG = "v"

    def __init__(self, secret, route_url):
        """Create a new BlockURLService object.

        :param secret: The secret to sign and check args with
        :param route_url: The pyramid `request.route_url` function
        """
        self._secret = secret
        self._route_url = route_url

    def route_url(self, route_name, *elements, **kw):
        """Get a secure version of route to our own app.

        This works identically to the Pyramid `Request.route_url()` function
        with the exception that the parameters are modified in place to sign
        them. This signature can be checked with `is_secure()`.
        """

        args = kw.get("_query")
        if args is None:
            raise ValueError("You must provide some parameters to sign")

        # Include this to allow us to cope with breaking changes in the
        # future if we ever decide to make some.
        args[self.VERSION_ARG] = "1"

        # We really should include the elements in the hash, but at present
        # we only have one link, and it has no elements.
        args[self.TOKEN_ARG] = self._hash_args(route_name, args)

        return self._route_url(route_name, *elements, **kw)

    def is_secure(self, request):
        """Check if a request was signed correctly.

        :param request: A pyramid Request object to check
        :rtype: bool
        """
        args = request.GET

        if self.TOKEN_ARG not in args:
            return False

        version = args.get(self.VERSION_ARG)
        if version != "1":
            return False

        without_token = dict(args)
        token = without_token.pop(self.TOKEN_ARG)

        return token == self._hash_args(request.matched_route.name, without_token)

    def _hash_args(self, route_name, args):
        digest = sha256()

        digest.update(self._secret.encode("utf-8"))
        digest.update(route_name.encode("utf-8"))

        for key, value in sorted(args.items()):
            digest.update(key.encode("utf-8"))
            digest.update(value.encode("utf-8"))

        return digest.hexdigest()


def factory(_context, request):
    return SecureLinkService(
        secret=request.registry.settings["checkmate_secret"],
        route_url=request.route_url,
    )
