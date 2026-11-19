    def create_booking(self, user_id: str, slot_id: str) -> dict:
        """
        Create a booking for a given user and slot.

        If the backend indicates that the user's email verification is pending,
        the method returns a friendly message instead of the normal booking
        payload. The caller can inspect the ``verification_pending`` key in the
        response to decide how to proceed.
        """
        payload = {"user_id": user_id, "slot_id": slot_id}
        response = self.client.post("/bookings", json=payload)
        response.raise_for_status()
        data = response.json()

        # The backend may include a ``verification_pending`` flag when the
        # user's email address has not been verified yet. Surface this to the
        # caller with a clear message.
        if data.get("verification_pending"):
            return {
                "verification_pending": True,
                "message": "Please verify your email before the booking is finalised."
            }

        return data