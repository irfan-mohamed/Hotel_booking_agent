from .payment_gateway import PaymentGateway
from .room_allocator import RoomAllocator
from ..errors import VerificationPendingError
    def create_booking(self, booking, user, payment_info):
        \"\"\"Create a new booking and handle downstream processes.\"

        This method now ensures that a booking is verified before any
        downstream actions (payment processing, room allocation, etc.) are
        performed. If the booking has not been verified, a
        :class:`VerificationPendingError` is raised with a user‑friendly
        message.\"
        # Guard against unverified bookings
        if not getattr(booking, \"is_verified\", False):
            raise VerificationPendingError(
                \"Booking cannot be approved because verification is still pending.\"
            )

        # Existing implementation...
        self.payment_gateway.process(payment_info)
        self.room_allocator.allocate(booking.room_type)
        booking.save()

    # Optional explicit approval method for clarity
    def approve_booking(self, booking):
        \"\"\"Approve a booking after verification.\n+\n+        This helper can be used by callers that separate creation from
        approval logic. It re‑uses the same verification guard.\n+        \"\"\"
        if not getattr(booking, \"is_verified\", False):
            raise VerificationPendingError(
                \"Booking cannot be approved because verification is still pending.\"
            )
        # Perform any additional approval steps here (e.g., notifications)
        return True