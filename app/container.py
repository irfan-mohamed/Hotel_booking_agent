from .repositories import UserRepository, BookingRepository, EmailVerificationRepository
from .services import UserService, BookingService, EmailVerificationService
        # Email verification components
        self.email_verification_repository = EmailVerificationRepository()
        self.email_verification_service = EmailVerificationService(
            self.email_verification_repository
        )