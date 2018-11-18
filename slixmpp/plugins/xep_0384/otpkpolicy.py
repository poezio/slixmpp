"""
    Slixmpp: The Slick XMPP Library

    Shamelessly copied from Syndace's python-omemo examples.
"""

import omemo


class KeepingOTPKPolicy(omemo.OTPKPolicy):
    @staticmethod
    def decideOTPK(preKeyMessages):
        # Always keep the OTPK.
        # This is the unsafest behaviour possible and should be avoided at all costs.
        return True
