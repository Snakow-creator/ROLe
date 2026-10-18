from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from beanie import PydanticObjectId

from migrations.boards import migrate_tasks_to_boards
from tasks import handler as task_handlers
from test_board_creation import make_client, board_database


@pytest.mark.parametrize('title', ['Простые', 'Своя доска'])
def test_delete_board_removes_all_own_tasks_and_preserves_other_data(database, title):
    db, _ = database
    board_id = db.boards.insert_one({'username': 'alice', 'title': title}).inserted_id
    other_board_id = db.boards.insert_one({'username': 'alice', 'title': 'Другая'}).inserted_id
    foreign_board_id = db.boards.insert_one({'username': 'bob', 'title': title}).inserted_id
    db.users.insert_one({'name': 'alice', 'Spoints': 250, 'xp': 150, 'level': 2, 'mul': 1.02})
    user_before = db.users.find_one({'name': 'alice'})
    for changes in [
        {'completed': False}, {'completed': True}, {'inactive': True},
        {'date': datetime.now(timezone.utc) + timedelta(days=10)},
    ]:
        db.tasks.insert_one({'user': 'alice', 'board_id': str(board_id), **changes})
    db.tasks.insert_many([
        {'user': 'alice', 'board_id': str(other_board_id)},
        {'user': 'bob', 'board_id': str(foreign_board_id)},
        # Even a malformed foreign task referencing this board is outside scope.
        {'user': 'bob', 'board_id': str(board_id)},
    ])
    with make_client() as client:
        response = client.delete(f'/delete/board/{board_id}')
        assert response.status_code == 200
        assert response.json()['deleted_tasks'] == 4
        assert response.json()['board_id'] == str(board_id)
        assert response.json()['title'] == title
        assert client.delete(f'/delete/board/{board_id}').status_code == 404
    assert db.boards.count_documents({}) == 2
    assert db.tasks.count_documents({}) == 3
    assert db.tasks.count_documents({'user': 'alice', 'board_id': str(board_id)}) == 0
    assert db.users.find_one({'name': 'alice'}) == user_before


def test_empty_last_board_can_be_deleted(database):
    db, _ = database
    board_id = db.boards.insert_one({'username': 'alice', 'title': 'Пустая'}).inserted_id
    with make_client() as client:
        response = client.delete(f'/delete/board/{board_id}')
    assert response.status_code == 200
    assert response.json()['deleted_tasks'] == 0
    assert db.boards.count_documents({}) == 0


@pytest.mark.parametrize('owner', ['bob', None])
def test_foreign_or_missing_board_does_not_delete_tasks(database, owner):
    db, _ = database
    board_id = PydanticObjectId()
    if owner:
        db.boards.insert_one({'_id': board_id, 'username': owner, 'title': 'Чужая'})
    task_id = db.tasks.insert_one({'user': 'alice', 'board_id': str(board_id)}).inserted_id
    with make_client() as client:
        assert client.delete(f'/delete/board/{board_id}').status_code == 404
    assert db.tasks.find_one({'_id': task_id}) is not None
    assert db.boards.count_documents({}) == int(owner is not None)


def test_unauthenticated_or_invalid_deletion_does_not_change_data(database):
    db, _ = database
    board_id = db.boards.insert_one({'username': 'alice', 'title': 'Доска'}).inserted_id
    with make_client(authenticated=False) as client:
        assert client.delete(f'/delete/board/{board_id}').status_code == 401
    with make_client() as client:
        assert client.delete('/delete/board/invalid').status_code == 422
    assert db.boards.count_documents({}) == 1


def test_failed_task_cleanup_keeps_board_for_retry(database, monkeypatch):
    db, collections = database
    board_id = db.boards.insert_one({'username': 'alice', 'title': 'Доска'}).inserted_id
    db.tasks.insert_one({'user': 'alice', 'board_id': str(board_id)})
    cleanup = collections['tasks'].delete_many
    monkeypatch.setattr(collections['tasks'], 'delete_many', AsyncMock(side_effect=RuntimeError('DB unavailable')))
    with make_client() as client:
        with pytest.raises(RuntimeError, match='DB unavailable'):
            client.delete(f'/delete/board/{board_id}')
        assert db.boards.count_documents({}) == 1
        assert db.tasks.count_documents({}) == 1
        monkeypatch.setattr(collections['tasks'], 'delete_many', cleanup)
        assert client.delete(f'/delete/board/{board_id}').status_code == 200
    assert db.boards.count_documents({}) == db.tasks.count_documents({}) == 0


@pytest.mark.asyncio
async def test_reload_and_migration_do_not_recreate_deleted_board(board_database, monkeypatch):
    db = board_database
    board_id = db.boards.insert_one({'username': 'alice', 'title': 'Простые', 'order': 0}).inserted_id
    db.tasks.insert_one({'user': 'alice', 'board_id': str(board_id), 'completed': True})
    monkeypatch.setattr(task_handlers.task_service, 'update', AsyncMock())
    monkeypatch.setattr(task_handlers.task_service.task_repo, 'get_user_tasks', AsyncMock(return_value=[]))
    with make_client() as client:
        assert client.delete(f'/delete/board/{board_id}').status_code == 200
        assert client.get('/tasks').json()['boards'] == []
        await migrate_tasks_to_boards()
        assert client.get('/tasks').json()['boards'] == []


@pytest.mark.parametrize('deleted_index', [0, 1, 2])
def test_deletion_compacts_order_and_new_board_uses_length(board_database, deleted_index):
    db = board_database
    ids = db.boards.insert_many([
        {'username': 'alice', 'title': 'Первая', 'order': 0},
        {'username': 'alice', 'title': 'Средняя', 'order': 1},
        {'username': 'alice', 'title': 'Последняя', 'order': 2},
    ]).inserted_ids
    foreign_id = db.boards.insert_one({'username': 'bob', 'title': 'Чужая', 'order': 2}).inserted_id
    with make_client() as client:
        assert client.delete(f'/delete/board/{ids[deleted_index]}').status_code == 200
        remaining_ids = [board_id for board_id in ids if board_id != ids[deleted_index]]
        assert [db.boards.find_one({'_id': board_id})['order'] for board_id in remaining_ids] == [0, 1]
        assert db.boards.find_one({'_id': foreign_id})['order'] == 2
        assert client.delete(f'/delete/board/{ids[deleted_index]}').status_code == 404
        assert [db.boards.find_one({'_id': board_id})['order'] for board_id in remaining_ids] == [0, 1]
        response = client.post('/add/board', json={'title': 'Новая'})
    assert response.status_code == 201
    assert response.json()['board']['order'] == 2
    assert sorted(board['order'] for board in db.boards.find({'username': 'alice'})) == [0, 1, 2]


@pytest.mark.parametrize('board', [None, SimpleNamespace(username='bob')])
def test_task_cannot_be_created_on_deleted_or_foreign_board(monkeypatch, board):
    monkeypatch.setattr(task_handlers.task_service.board_repo, 'get', AsyncMock(return_value=board))
    insert = AsyncMock()
    monkeypatch.setattr(task_handlers.task_service.task_repo, 'insert_task', insert)
    with make_client() as client:
        response = client.post('/add/task', json={
            'title': 'Квест', 'description': '',
            'board_id': '0123456789abcdef01234567', 'date': None,
        })
    assert response.status_code == 404
    insert.assert_not_awaited()


def test_task_rejects_invalid_board_id(monkeypatch):
    insert = AsyncMock()
    monkeypatch.setattr(task_handlers.task_service.task_repo, 'insert_task', insert)
    with make_client() as client:
        response = client.post('/add/task', json={
            'title': 'Квест', 'description': '', 'board_id': 'invalid', 'date': None,
        })
    assert response.status_code == 422
    insert.assert_not_awaited()


def test_task_can_be_created_on_owned_board_with_canonical_id(monkeypatch):
    board_id = PydanticObjectId('0123456789abcdef01234567')
    monkeypatch.setattr(task_handlers.task_service.board_repo, 'get', AsyncMock(return_value=SimpleNamespace(username='alice', id=board_id)))
    insert = AsyncMock()
    monkeypatch.setattr(task_handlers.task_service.task_repo, 'insert_task', insert)
    with make_client() as client:
        response = client.post('/add/task', json={
            'title': 'Квест', 'description': '', 'board_id': str(board_id).upper(), 'date': None,
        })
    assert response.status_code == 200
    insert.assert_awaited_once()
    data = insert.await_args.args[0]
    assert data['user'] == 'alice'
    assert data['board_id'] == str(board_id)
