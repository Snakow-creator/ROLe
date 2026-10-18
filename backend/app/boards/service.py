class BoardService:
    """Coordinate board creation and deletion while preserving order and plan history."""

    def __init__(self, board_repo, task_repo, planning_repository):
        self.board_repo = board_repo
        self.task_repo = task_repo
        self.planning_repository = planning_repository

    async def create_board(self, creds, name):
        """Choose the next board position and save the board."""
        order = await self.board_repo.count_user_boards(name)
        return await self.board_repo.insert_board({**creds.model_dump(), "username": name, "order": order})

    async def _preserve_plan_history(self, board_id, name):
        """Copy quest completion into plan entries before the quests are removed."""
        tasks = await self.task_repo.get_plan_tasks_by_board(board_id, name)
        for task in tasks:
            await self.planning_repository.update_entry(name, task["plan_entry_id"], {
                "board_id": None,
                "completed": task.get("completed", False),
                "complete_date": task.get("complete_date"),
            })

    async def delete_board(self, board_id, name):
        """Delete a user's board and its quests, keeping plan history and display order."""
        board = await self.board_repo.get_owned_board(board_id, name)
        if board is None:
            return None
        await self._preserve_plan_history(board_id, name)
        await self.planning_repository.detach_board_templates(name, board_id)
        await self.planning_repository.detach_board_entries(name, board_id)
        # Keep the board available for retry until its task cleanup succeeds.
        deleted_tasks = await self.task_repo.delete_by_board(board_id, name)
        if await self.board_repo.delete_board(board_id, name):
            await self.board_repo.compact_order(name, board.get("order", 0))
        return {"title": board["title"], "deleted_tasks": deleted_tasks}
