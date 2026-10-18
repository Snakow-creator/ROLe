from beanie import PydanticObjectId as ObjectId
from pymongo.errors import DuplicateKeyError

from base.config import BaseRepository
from models.models import PlanEntry, PlanTemplate


class PlanningRepository(BaseRepository):
    """Database operations for plan entries and their repeat templates."""

    def __init__(self):
        """Set PlanEntry as the primary repository model."""
        super().__init__(PlanEntry)

    @staticmethod
    def _collection(model):
        """Return the MongoDB collection for the given model."""
        return model.get_pymongo_collection()

    async def _documents(self, model, query):
        """Return all model documents matching the query as a list."""
        return await self._collection(model).find(query).to_list(length=None)

    async def get_entry(self, user, entry_id):
        """Find a plan entry by ID among the given user's entries."""
        return await self._collection(PlanEntry).find_one({"_id": ObjectId(entry_id), "user": user})

    async def get_week_entries(self, user, week, *, active_only=False):
        """Return the user's weekly entries, excluding cancelled ones when active_only is set."""
        query = {"user": user, "week_start": week}
        if active_only:
            query["cancelled"] = False
        return await self._documents(PlanEntry, query)

    async def get_series_entries(self, user, series_id, from_week):
        """Return the user's series entries from the given week onward, inclusive."""
        return await self._documents(PlanEntry, {
            "user": user, "series_id": series_id, "week_start": {"$gte": from_week},
        })

    async def get_occurrence(self, series_id, week):
        """Find the entry for the given series and week."""
        return await self._collection(PlanEntry).find_one({"series_id": series_id, "week_start": week})

    async def get_active_template_entry(self, user, template_id, week):
        """Find the user's non-cancelled entry for the given template and week."""
        return await self._collection(PlanEntry).find_one({
            "user": user, "template_id": template_id, "week_start": week, "cancelled": False,
        })

    async def get_templates(self, user=None, *, starts_by=None):
        """Return templates, optionally filtering by owner and an inclusive start date cutoff."""
        query = {}
        if user is not None:
            query["user"] = user
        if starts_by is not None:
            query["starts_on"] = {"$lte": starts_by}
        return await self._documents(PlanTemplate, query)

    async def get_template(self, user, template_id):
        """Find a template by ID among the given user's templates."""
        return await self._collection(PlanTemplate).find_one({"_id": ObjectId(template_id), "user": user})

    async def get_entries_to_repair(self, user, from_week, through_week):
        """Select tasks linked to boards within an inclusive week range for quest synchronization."""
        query = {
            "kind": "task", "board_id": {"$type": "string"},
            "week_start": {"$gte": from_week, "$lte": through_week},
        }
        if user is not None:
            query["user"] = user
        return await self._documents(PlanEntry, query)

    async def upsert_occurrence(self, fields):
        """Create a weekly series entry if missing and return it without overwriting an existing entry."""
        query = {"series_id": fields["series_id"], "week_start": fields["week_start"]}
        document = PlanEntry.model_validate({"_id": ObjectId(), **fields}).model_dump(by_alias=True)
        try:
            await self._collection(PlanEntry).update_one(query, {"$setOnInsert": document}, upsert=True)
        except DuplicateKeyError:
            # A concurrent request already created this series entry for the same week.
            pass
        return await self._collection(PlanEntry).find_one(query)

    async def insert_template(self, template):
        """Insert a new template for a repeating entry."""
        return await self._collection(PlanTemplate).insert_one(template)

    async def update_template(self, user, template_id, values):
        """Update the supplied fields of the user's template."""
        return await self._collection(PlanTemplate).update_one(
            {"_id": ObjectId(template_id), "user": user}, {"$set": values},
        )

    async def advance_template_cursor(self, template_id, week):
        """Advance the template's last generated week without moving it backward."""
        # $max preserves the later week during concurrent updates.
        return await self._collection(PlanTemplate).update_one(
            {"_id": template_id}, {"$max": {"generated_through": week}},
        )

    async def update_entry(self, user, entry_id, values):
        """Update the supplied fields of the user's plan entry."""
        return await self._collection(PlanEntry).update_one(
            {"_id": ObjectId(entry_id), "user": user}, {"$set": values},
        )

    async def link_series_template(self, user, series_id, from_week, template_id):
        """Link the user's series entries to a template from the given week onward, inclusive."""
        return await self._collection(PlanEntry).update_many(
            {"user": user, "series_id": series_id, "week_start": {"$gte": from_week}},
            {"$set": {"template_id": template_id}},
        )

    async def detach_goal_parts(self, user, goal_id):
        """Remove the goal link from the user's tasks while preserving the tasks."""
        return await self._collection(PlanEntry).update_many(
            {"user": user, "goal_id": goal_id}, {"$set": {"goal_id": None}},
        )

    async def detach_goal_templates(self, user, goal_template_id):
        """Remove links between the user's task templates and the given goal template."""
        return await self._collection(PlanTemplate).update_many(
            {"user": user, "goal_template_id": goal_template_id}, {"$set": {"goal_template_id": None}},
        )

    async def detach_board_templates(self, user, board_id):
        """Remove the board link from the user's plan templates."""
        return await self._collection(PlanTemplate).update_many(
            {"user": user, "board_id": str(board_id)}, {"$set": {"board_id": None}},
        )

    async def detach_board_entries(self, user, board_id):
        """Remove the board link from the user's plan occurrences."""
        return await self._collection(PlanEntry).update_many(
            {"user": user, "board_id": str(board_id)}, {"$set": {"board_id": None}},
        )
