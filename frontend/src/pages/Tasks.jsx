import { useState, useEffect, useRef } from "react";

import FormCreateTask from "../components/FormCreateTask";
import { getTasks, completeTask, unCompleteTask, deleteTask } from "../services/apiService/tasks";

import { cn } from "../hooks/utils";
import { quests_types } from "../data/data";


function Task(creds) {
  // className objects
  const [classTitle, setClassTitle] = useState("");

  const [showSubmit, setShowSubmit] = useState(false);
  const [isSubmit, setIsSubmit] = useState(false);
  const [trashSrc, setTrashSrc] = useState("/task/trash.png");

  function visibleSubmit() {
    setShowSubmit(true);
    setClassTitle("transform transition-transform duration-400 translate-x-5 sm:w-48");
  };

  const hideSubmit = async () => {
    setClassTitle("transform transition-transform duration-400 translate-x-0 sm:w-52");
    setShowSubmit(null);
  };

  const submitTask = async () => {
    if (isSubmit) {
      setIsSubmit(false);
      await unCompleteTask({
        id: creds.id
      })
    } else {
      setIsSubmit(true);
      await completeTask({
        id: creds.id
      })
    }
  }

  const delTask = async () => {
    setTrashSrc("/task/trash_hover.png");
    await deleteTask({
      id: creds.id
    })

    creds.onUpdate();
  }

  return (
    // task container
    <div className="relative flex items-center space-x-1 bg-[#ffffff] text-[15px] font-normal rounded-md px-3 py-1 w-full border border-[#F1F1F1] hover:outline-2 hover:outline-blue-400 box-border shadow transition-transform"
      onMouseEnter={() => { if (!isSubmit) visibleSubmit() }}
      onMouseLeave={() => { if (!isSubmit) hideSubmit() }}>
      {/* submit button */}
      <button
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
        className={cn("absolute right-2 z-[10000] transition-opacity duration-300 cursor-pointer h-[25px] w-[25px]",
          showSubmit ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onMouseEnter={() => { setTrashSrc("/task/trash_hover.png") }}
        onMouseLeave={() => { setTrashSrc("/task/trash.png") }}
        onMouseDown={() => { setTrashSrc("/task/trash_active.png") }}
        onClick={delTask}>

        <img src={trashSrc} />
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
        "container bg-[#F9FAFE] rounded-2xl py-3 px-2 w-[275px] shadow border border-[#E5E9F0]",
        creds.className,
      )}
    >
      <div className="font-extrabold">
        <h2 className="ml-4">{creds.title}</h2>

        <div className="mt-2 space-y-2">
          {creds.tasks
            .filter(task => task.type === creds.type)
            .map(({ _id, title, description }) => (
              <Task key={_id}
                    id={_id}
                    title={title}
                    description={description}
                    onUpdate={creds.onUpdate}/>
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
                onUpdate={creds.onUpdate}
                type={creds.type} />
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
  const [tasks, setTasks] = useState([]);
  const [typeTasks, setTypeTasks] = useState([]);

  const fetchTasks = async () => {
    await getTasks({onFinish: data => {
        setTasks(data.tasks);
        setTypeTasks(data.type_tasks);
      }
     });
  }

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleUpdate = async () => {
    fetchTasks();
  }

  return (
    <div className="flex items-start ml-2 mt-4 space-x-3">
      {typeTasks.map(type => (
        <CanbanDesk
          key={type}
          title={quests_types[type]}
          type={type}
          tasks={tasks}
          onUpdate={handleUpdate}/>
      ))}
    </div>
  );
};
