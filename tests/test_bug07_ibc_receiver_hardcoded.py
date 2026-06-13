"""Bug #7 — HIGH | x/wstaking | IbcTransferFromRegionTreasure
Issue: https://github.com/openmetaearth/me-hub/issues/1246

Receiver is hardcoded as the treasury (sender) address instead of
msg.Receiver. On the destination chain, funds arrive at a module-
account-derived address with no private key — permanently burned.

Vulnerable pattern (msg_server_ibc_transfer_from_region_treasure.go:34):
    treasureAddress,    // receiver <- SAME as sender! msg.Receiver ignored

Fix: use msg.Receiver as the IBC transfer destination.
"""

import pytest


def new_msg_transfer(
    source_port: str,
    source_channel: str,
    token: str,
    sender: str,
    receiver: str,
) -> dict:
    return {
        "source_port": source_port,
        "source_channel": source_channel,
        "token": token,
        "sender": sender,
        "receiver": receiver,
    }


def ibc_transfer_buggy(
    treasure_address: str,
    msg_receiver: str,
    msg_source_port: str,
    msg_source_channel: str,
    msg_token: str,
) -> dict:
    """Buggy: receiver is hardcoded as treasury address."""
    return new_msg_transfer(
        msg_source_port,
        msg_source_channel,
        msg_token,
        treasure_address,       # sender — correct
        treasure_address,       # receiver — WRONG! should be msg_receiver
    )


def ibc_transfer_fixed(
    treasure_address: str,
    msg_receiver: str,
    msg_source_port: str,
    msg_source_channel: str,
    msg_token: str,
) -> dict:
    """Fixed: uses msg.Receiver for destination."""
    if not msg_receiver:
        raise ValueError("receiver address cannot be empty")
    return new_msg_transfer(
        msg_source_port,
        msg_source_channel,
        msg_token,
        treasure_address,       # sender — correct
        msg_receiver,           # receiver — correct
    )


class TestBug07IbcReceiverHardcoded:

    TREASURY = "me1treasurymoduleaddress"
    USER = "cosmos1userreceiveraddress"

    def test_buggy_receiver_equals_sender(self):
        """Buggy: receiver is always the treasury, not the user."""
        msg = ibc_transfer_buggy(
            self.TREASURY, self.USER,
            "transfer", "channel-0", "1000umec",
        )
        assert msg["sender"] == self.TREASURY
        assert msg["receiver"] == self.TREASURY  # Bug! Should be USER
        assert msg["receiver"] != self.USER

    def test_fixed_receiver_is_user(self):
        """Fixed: receiver is the intended destination."""
        msg = ibc_transfer_fixed(
            self.TREASURY, self.USER,
            "transfer", "channel-0", "1000umec",
        )
        assert msg["sender"] == self.TREASURY
        assert msg["receiver"] == self.USER  # Correct

    def test_funds_burned_on_dest_chain(self):
        """Module-account-derived addresses have no private key on the
        destination chain — funds are permanently unspendable."""
        msg = ibc_transfer_buggy(
            self.TREASURY, self.USER,
            "transfer", "channel-0", "1000umec",
        )
        # The receiver is a module address, not a user address
        assert msg["receiver"].startswith("me1")  # module addr prefix
        # No one controls this address on the destination chain

    def test_fixed_validates_empty_receiver(self):
        """Fixed version rejects empty receiver."""
        with pytest.raises(ValueError, match="receiver address cannot be empty"):
            ibc_transfer_fixed(
                self.TREASURY, "",
                "transfer", "channel-0", "1000umec",
            )

    def test_msg_receiver_field_completely_unused_buggy(self):
        """Demonstrates that msg.Receiver is entirely ignored."""
        msg1 = ibc_transfer_buggy(
            self.TREASURY, "cosmos1alice",
            "transfer", "channel-0", "1000umec",
        )
        msg2 = ibc_transfer_buggy(
            self.TREASURY, "cosmos1bob",
            "transfer", "channel-0", "1000umec",
        )
        # Different msg.Receiver but same output
        assert msg1["receiver"] == msg2["receiver"] == self.TREASURY
