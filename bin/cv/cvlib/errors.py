class CvError(Exception):
    """A generation error worth stopping for.

    Raised with a message that names the offending field, so the user can
    fix cv.toml without reading the generator.
    """
