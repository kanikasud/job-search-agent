"""SQLAlchemy ORM model for the canonical job listing schema."""

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class JobListing(Base):
    """Canonical job record persisted to SQLite.

    Both sources normalise their fields into this structure before insertion:
      - The Muse: ``name`` → ``title``, ``publication_date`` → ``posted_at``
      - Remote OK: ``position`` → ``title``, ``date`` → ``posted_at``
    """

    __tablename__ = "job_listings"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_source_source_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    # Stored as a JSON array of strings; e.g. ["Python", "Remote"]
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # ISO 8601 date/datetime string as returned by the source API
    posted_at: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<JobListing id={self.id} source={self.source!r} title={self.title!r}>"
