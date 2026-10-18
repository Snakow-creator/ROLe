import { useState, useEffect, useRef, useCallback } from "react";

import FormCreateTask from "../components/forms/FormCreateTask";
import FormCreateBoard from "../components/forms/FormCreateBoard";
import BoardInfo from "../components/boards/BoardInfo";
import DeleteBoardDialog, { TrashIcon } from "../components/boards/DeleteBoardDialog";
import { deleteBoard } from "../services/apiService/boards";
import Spinner from "../components/Spinner";
import { getTasks, completeTask, unCompleteTask, deleteTask } from "../services/apiService/tasks";
import { mergeTaskRefresh, startTaskAutoRefresh } from '../services/apiService/taskRefresh';

import { cn } from "../hooks/utils";
import { useNotify } from "../context/NotificationContext";
import { TaskSubmitNotification } from "../components/webNotifications/types/TaskNotification";
import { UpLevelNotification } from "../components/webNotifications/types/UpLevelNotification";
import { TaskUnSubmitNotification } from "../components/webNotifications/types/TaskUnSubmitNotification";
import { DownLevelNotification } from "../components/webNotifications/types/DownLevelNotification";
import { DeleteTaskNotification } from "../components/webNotifications/types/DeleteTaskNotification";
import { WeeklyBonusNotification } from "../components/webNotifications/types/WeeklyBonusNotification";
import { RevokeWeeklyBonusNotification } from "../components/webNotifications/types/RevokeWeeklyBonusNotification";
import { CreateTaskNotification } from "../components/webNotifications/types/CreateTaskNotification";
import { ErrorCreateTaskNotification } from "../components/webNotifications/types/ErrorCreateTaskNotification";
import { CreateBoardNotification } from "../components/webNotifications/types/CreateBoardNotification";
import { DeleteBoardNotification } from "../components/webNotifications/types/DeleteBoardNotification";
import { ErrorTaskNotification } from '../components/webNotifications/types/ErrorTaskNotification';
import { ErrorLoadTasksNotification } from '../components/webNotifications/types/ErrorLoadTasksNotification';
import { getRequestErrorMessage, isSessionExpiredError } from '../services/apiService/requestErrors';


function Task(creds) {
  // className objects
  const [classTitle, setClassTitle] = useState("");
  const [showSubmit, setShowSubmit] = useState(false);
  const isSubmit = Boolean(creds.completed);
  const [trashSrc, setTrashSrc] = useState("/task/trash.png");
  const [isPending, setIsPending] = useState(false);
  const pendingRef = useRef(false);
  const { push } = useNotify();


  function visibleSubmit() {
    setShowSubmit(true);
    setClassTitle("transform transition-transform duration-400 translate-x-5 sm:w-48");
  };

  const hideSubmit = async () => {
    setClassTitle("transform transition-transform duration-400 translate-x-0 sm:w-52");
    setShowSubmit(null);
  };

  const submitTask = async () => {
    if (pendingRef.current) return;
    pendingRef.current = true;
    setIsPending(true);
    creds.onMutationStart();
    const action = isSubmit ? 'uncomplete' : 'complete';
    try {
      const data = await (isSubmit ? unCompleteTask : completeTask)({ id: creds.id });
      creds.onStatusChange(creds.id, !isSubmit);
      if (isSubmit) {
        creds.onNoticeReturnTask(data.notice);
        if (data.notice_down_level) creds.onNoticeDownLevel(data.notice_down_level);
        if (data.notice_weekly_revoke_bonus) creds.onNoticeRevokeWeeklyBonus(data.notice_weekly_revoke_bonus);
      } else {
        creds.onNotice(data.notice);
        if (data.notice_up_level) creds.onNoticeUpLevel(data.notice_up_level);
        if (data.notice_weekly_claim_bonus) creds.onNoticeWeeklyBonus(data.notice_weekly_claim_bonus);
      }
    } catch (error) {
      if (!isSessionExpiredError(error)) push(new ErrorTaskNotification(action, error));
    } finally {
      pendingRef.current = false;
      setIsPending(false);
      creds.onMutationEnd();
    }
  }

  const delTask = async () => {
    if (pendingRef.current) return;
    pendingRef.current = true;
    setIsPending(true);
    creds.onMutationStart();
    try {
      const data = await deleteTask({ id: creds.id });
      creds.onNoticeDeleteTask(data.notice);
      await creds.onUpdate();
    } catch (error) {
      if (!isSessionExpiredError(error)) push(new ErrorTaskNotification('delete', error));
    } finally {
      pendingRef.current = false;
      setIsPending(false);
      setTrashSrc('/task/trash.png');
      creds.onMutationEnd();
    }
  }

  return (
    // task container
    <div className="relative flex items-center space-x-1 bg-[#ffffff] text-[15px] font-normal rounded-md px-3 py-1 w-full border border-[#F1F1F1] hover:outline-2 hover:outline-blue-400 box-border shadow transition-transform"
      onMouseEnter={() => { if (!isSubmit) visibleSubmit() }}
      onMouseLeave={() => { if (!isSubmit) hideSubmit() }}>
      {/* submit button */}
      <button
        type="button"
        disabled={isPending}
        aria-label={`${isSubmit ? 'Отменить выполнение квеста' : 'Завершить квест'} «${creds.title}»`}
        aria-pressed={isSubmit}
        className={cn("absolute border w-4 h-4 text-xs rounded-full cursor-pointer transition-opacity duration-300",
          showSubmit ? "opacity-100" : "opacity-0 pointer-events-none",
          isSubmit && "bg-green-300 border-green-300",
        )}
        onClick={submitTask}
      >
        {isSubmit && "✔"}
      </button>

      <span className={cn(
        "truncate sm:w-52 z-10",
        classTitle
      )}>
        {creds.title}
      </span>

      {/* trash button */}
      <button
        type="button"
        disabled={isPending}
        aria-label={`Удалить квест «${creds.title}»`}
        className={cn("absolute right-2 z-40 transition-opacity duration-300 cursor-pointer h-[25px] w-[25px]",
          showSubmit ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onMouseEnter={() => { setTrashSrc("/task/trash_hover.png") }}
        onMouseLeave={() => { setTrashSrc("/task/trash.png") }}
        onMouseDown={() => { setTrashSrc("/task/trash_active.png") }}
        onClick={delTask}>

        <img src={trashSrc} alt="" />
      </button>
    </div>
  )
};


function CanbanDesk(creds) {
  const [isFormCreateTask, setIsFormCreateTask] = useState(false);

  const formCreateTaskRef = useRef(null);

  useEffect(() => {
    if (!isFormCreateTask) return;

    const handleClickOutside = (e) => {
      if (formCreateTaskRef.current && !formCreateTaskRef.current.contains(e.target)) {
        setIsFormCreateTask(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isFormCreateTask])

  const onClickCancelButton = () => {
    setIsFormCreateTask(false);
  }

  return (
    <div
      className={cn(
        "container bg-[#F9FAFE] flex-shrink-0 rounded-2xl py-3 px-2 w-[275px] 2xl:w-[320px] shadow border border-[#E5E9F0]",
        creds.className,
      )}
    >
      <div className="font-extrabold">
        <div className="flex items-center justify-between gap-2">
          <h2 className="ml-4 break-words min-w-0">{creds.title}</h2>
          <button
            type="button"
            aria-label={`Удалить доску «${creds.title}»`}
            title="Удалить доску"
            onClick={creds.onDeleteBoard}
            className="mr-1 flex h-6 w-6 shrink-0 cursor-pointer items-center justify-center rounded-md text-[#7C8AA0] hover:bg-red-50 hover:text-red-600 focus-visible:outline-2 focus-visible:outline-red-500"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
        <BoardInfo points={creds.award_points} xp={creds.award_xp} days={creds.task_expire_days} />

        <div className="mt-2 space-y-2 w-full">
          {creds.tasks
            .filter(task => task.board_id === creds.board_id)
            .map(({ _id, title, description, completed }) => (
              <Task key={_id}
                id={_id}
                title={title}
                description={description}
                completed={completed}
                onStatusChange={creds.onStatusChange}
                onMutationStart={creds.onMutationStart}
                onMutationEnd={creds.onMutationEnd}
                onUpdate={creds.onUpdate}
                onNotice={creds.onNotice}
                onNoticeUpLevel={creds.onNoticeUpLevel}
                onNoticeReturnTask={creds.onNoticeReturnTask}
                onNoticeDownLevel={creds.onNoticeDownLevel}
                onNoticeDeleteTask={creds.onNoticeDeleteTask}
                onNoticeWeeklyBonus={creds.onNoticeWeeklyBonus}
                onNoticeRevokeWeeklyBonus={creds.onNoticeRevokeWeeklyBonus} />
            ))
          }
        </div>

        {/* create quest */}
        {
          isFormCreateTask ? (
            <div ref={formCreateTaskRef}
              onClick={e => {
                if (e.target === e.currentTarget) {
                  setIsFormCreateTask(false)
                }
              }}>
              <FormCreateTask
                onClickCancelButton={onClickCancelButton}
                onNoticeCreateTask={creds.onNoticeCreateTask}
                onNoticeErrorCreateTask={creds.onNoticeErrorCreateTask}
                onUpdate={creds.onUpdate}
                onMutationStart={creds.onMutationStart}
                onMutationEnd={creds.onMutationEnd}
                board_id={creds.board_id} />
            </div>
          ) : (
            <button
              className="mt-2 text-[#7C8AA0] p-1 pl-2 w-full rounded-md text-left cursor-pointer hover:bg-[#EEF2F7] active:bg-[#E5E9F0]"
              type="button"
              onClick={() => { setIsFormCreateTask(true) }}>
              ＋ Добавить квест
            </button>
          )
        }
      </div>
    </div>
  )
};




export default function Tasks() {
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [tasks, setTasks] = useState([]);
  const [boards, setBoards] = useState([]);
  const [isFormCreateBoard, setIsFormCreateBoard] = useState(false);
  const [boardToDelete, setBoardToDelete] = useState(null);
  const [isDeletingBoard, setIsDeletingBoard] = useState(false);
  const [deleteBoardError, setDeleteBoardError] = useState('');
  const deletingBoardRef = useRef(false);
  const deletedBoardIdsRef = useRef(new Set());
  const createBoardButtonRef = useRef(null);
  const latestFetchRef = useRef(0);
  const activeFetchesRef = useRef(0);
  const pendingMutationsRef = useRef(0);
  const refreshPausedRef = useRef(false);

  const { push, removeByKey } = useNotify();


  const fetchTasks = useCallback(async ({ notifyError = true, background = false } = {}) => {
    if (background && (
      activeFetchesRef.current || pendingMutationsRef.current ||
      deletingBoardRef.current || refreshPausedRef.current
    )) return;
    const requestId = ++latestFetchRef.current;
    activeFetchesRef.current += 1;
    if (!background) setLoadError('');
    try {
      const response = await getTasks();
      if (requestId !== latestFetchRef.current) return;
      const nextTasks = response.data.tasks.filter(task => !deletedBoardIdsRef.current.has(task.board_id));
      const nextBoards = response.data.boards.filter(board => !deletedBoardIdsRef.current.has(board._id));
      setTasks(current => background ? mergeTaskRefresh(current, nextTasks, nextBoards) : nextTasks);
      setBoards(nextBoards);
      setLoadError('');
      refreshPausedRef.current = false;
      removeByKey('error_load_tasks');
      return response;
    } catch (error) {
      if (requestId !== latestFetchRef.current) return;
      if (isSessionExpiredError(error)) refreshPausedRef.current = true;
      if (background) return;
      setLoadError(getRequestErrorMessage(error, 'Не удалось загрузить доски и квесты.'));
      if (notifyError && !isSessionExpiredError(error)) {
        push(new ErrorLoadTasksNotification(error, () => fetchTasks()));
      }
    } finally {
      activeFetchesRef.current -= 1;
      if (requestId === latestFetchRef.current) setIsLoading(false);
    }
  }, [push, removeByKey]);

  useEffect(() => {
    fetchTasks();
    const stopRefresh = startTaskAutoRefresh(() => fetchTasks({ background: true }));
    return () => {
      stopRefresh();
      latestFetchRef.current += 1;
    };
  }, [fetchTasks]);

  const handleMutationStart = () => {
    pendingMutationsRef.current += 1;
    // A request started before this action must not overwrite its result.
    latestFetchRef.current += 1;
  };
  const handleMutationEnd = () => {
    pendingMutationsRef.current -= 1;
  };
  const handleTaskStatusChange = (id, completed) => {
    setTasks(current => current.map(task => task._id === id ? { ...task, completed } : task));
  };

  const handleNotice = async (notice) => {
    push(new TaskSubmitNotification(notice));
  }
  const handleNoticeUpLevel = async (notice) => {
    push(new UpLevelNotification(notice));
  }

  const handleNoticeReturnTask = async (notice) => {
    push(new TaskUnSubmitNotification(notice));
  }
  const handleNoticeDownLevel = async (notice) => {
    push(new DownLevelNotification(notice));
  }

  const handleNoticeDeleteTask = async (notice) => {
    push(new DeleteTaskNotification(notice));
  }

  const handleNoticeWeeklyBonus = async (notice) => {
    push(new WeeklyBonusNotification(notice));
  }

  const handleNoticeRevokeWeeklyBonus = async (notice) => {
    push(new RevokeWeeklyBonusNotification(notice));
  }

  const handleNoticeCreateTask = async (notice) => {
    push(new CreateTaskNotification(notice));
  }

  const handleNoticeErrorCreateTask = async (notice) => {
    push(new ErrorCreateTaskNotification(notice));
  }


  const handleUpdate = async () => {
    return fetchTasks();
  }

  const handleBoardCreated = (board) => {
    latestFetchRef.current += 1;
    setBoards(current => [...current, board].sort((left, right) =>
      left.order - right.order || left._id.localeCompare(right._id)
    ));
    setIsFormCreateBoard(false);
    push(new CreateBoardNotification());
  };

  const handleDeleteBoard = async () => {
    if (deletingBoardRef.current || !boardToDelete) return;
    const board = boardToDelete;
    deletingBoardRef.current = true;
    setIsDeletingBoard(true);
    handleMutationStart();
    setDeleteBoardError('');
    try {
      try {
        await deleteBoard(board._id);
      } catch (error) {
        const status = error.response?.status;
        if (status !== 404) {
          setDeleteBoardError(status === 401
            ? 'Войдите в аккаунт, чтобы удалить доску.'
            : 'Не удалось удалить доску. Попробуйте ещё раз.');
          return;
        }
        // An already deleted board must also disappear from this tab.
      }
      deletedBoardIdsRef.current.add(board._id);
      const response = await fetchTasks({ notifyError: false });
      if (!response) {
        setDeleteBoardError('Доска удалена, но не удалось обновить список. Повторите запрос.');
        return;
      }
      setBoardToDelete(null);
      push(new DeleteBoardNotification(board.title));
      createBoardButtonRef.current?.focus();
    } finally {
      deletingBoardRef.current = false;
      setIsDeletingBoard(false);
      handleMutationEnd();
    }
  };

  return (
    isLoading
      ? <Spinner />
      : <>
        {loadError && (
          <div role="alert" className="mx-2 mt-4 rounded-xl border border-red-100 bg-white px-4 py-3 text-sm text-red-700">
            <p>{loadError}</p>
            <button type="button" onClick={() => fetchTasks()} className="mt-2 cursor-pointer rounded-md border border-[#E5E9F0] px-3 py-1.5 font-semibold hover:bg-[#EEF2F7] focus-visible:outline-2 focus-visible:outline-blue-500">Повторить загрузку</button>
          </div>
        )}
        <div className="flex items-start ml-2 mt-4 space-x-3">
        {boards.map(board => (
          <CanbanDesk
            key={board._id}
            title={board.title}
            board_id={board._id}
            award_points={board.award_points}
            award_xp={board.award_xp}
            task_expire_days={board.task_expire_days}
            tasks={tasks}
            onDeleteBoard={() => {
              setDeleteBoardError('');
              setBoardToDelete(board);
            }}
            onUpdate={handleUpdate}
            onStatusChange={handleTaskStatusChange}
            onMutationStart={handleMutationStart}
            onMutationEnd={handleMutationEnd}
            onNotice={handleNotice}
            onNoticeUpLevel={handleNoticeUpLevel}
            onNoticeReturnTask={handleNoticeReturnTask}
            onNoticeDownLevel={handleNoticeDownLevel}
            onNoticeDeleteTask={handleNoticeDeleteTask}
            onNoticeWeeklyBonus={handleNoticeWeeklyBonus}
            onNoticeRevokeWeeklyBonus={handleNoticeRevokeWeeklyBonus}
            onNoticeCreateTask={handleNoticeCreateTask}
            onNoticeErrorCreateTask={handleNoticeErrorCreateTask} />

        ))}

        {isFormCreateBoard ? (
          <FormCreateBoard
            onCancel={() => setIsFormCreateBoard(false)}
            onCreated={handleBoardCreated}
          />
        ) : (
          <button
            ref={createBoardButtonRef}
            type="button"
            onClick={() => setIsFormCreateBoard(true)}
            className="flex h-11 w-[275px] flex-shrink-0 items-center gap-2 rounded-2xl border border-[#B8C2D2] bg-[#E5E7EB]/50 opacity-50 px-4 text-left font-semibold text-[#334155] shadow-sm cursor-pointer transition duration-150 ease-out hover:bg-[#E5E7EB]/80 hover:border-[#9CAAC0] hover:opacity-75 active:bg-[#D8DFEA]/90 active:border-[#8E9DB5] active:opacity-100 active:translate-y-px active:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#94A3B8] focus-visible:ring-offset-2 2xl:w-[320px]"
          >
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
            Добавить доску
          </button>
        )}

        {boardToDelete && (
          <DeleteBoardDialog
            board={boardToDelete}
            isDeleting={isDeletingBoard}
            error={deleteBoardError}
            onCancel={() => {
              if (!deletingBoardRef.current) setBoardToDelete(null);
            }}
            onConfirm={handleDeleteBoard}
          />
        )}

      </div>
      </>
  );
};
