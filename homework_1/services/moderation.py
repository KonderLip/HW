from repositories.moderation import ModerationRepository


class ModerationService:
    def __init__(self, repository: ModerationRepository):
        self.repository = repository

    def predict(
        self,
        is_verified_seller: bool,
        images_qty: int,
    ) -> bool:
        if is_verified_seller:
            return True

        return images_qty >= self.repository.min_images_for_unverified()
