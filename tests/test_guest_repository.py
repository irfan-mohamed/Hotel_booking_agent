class TestGuestRepository:

    def test_create_guest(
        self,
        guest_repository,
    ):
        guest = guest_repository.create(
            name="John Doe",
            email="john@example.com",
        )

        assert guest.id is not None
        assert guest.name == "John Doe"
        assert guest.email == "john@example.com"

    def test_get_guest_by_email(
        self,
        guest_repository,
    ):
        created = guest_repository.create(
            name="Jane Doe",
            email="jane@example.com",
        )

        result = guest_repository.get_by_email(
            "jane@example.com"
        )

        assert result is not None
        assert result.id == created.id

    def test_get_guest_by_id(
        self,
        guest_repository,
    ):
        created = guest_repository.create(
            name="Alice",
            email="alice@example.com",
        )

        result = guest_repository.get_by_id(
            created.id
        )

        assert result is not None
        assert result.email == "alice@example.com"

    def test_get_or_create_reuses_existing_guest(
        self,
        guest_repository,
    ):
        first = guest_repository.get_or_create(
            name="Bob",
            email="bob@example.com",
        )

        second = guest_repository.get_or_create(
            name="Bob Updated",
            email="bob@example.com",
        )

        assert first.id == second.id

    def test_get_missing_guest_returns_none(
        self,
        guest_repository,
    ):
        result = guest_repository.get_by_email(
            "missing@example.com"
        )

        assert result is None