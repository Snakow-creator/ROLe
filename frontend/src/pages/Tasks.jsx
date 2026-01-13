import { useState, useEffect, useRef } from "react";

import FormCreateTask from "../components/FormCreateTask";
import { getTasks, completeTask, unCompleteTask, deleteTask } from "../services/apiService/tasks";

// import { getMessageTask, getMessageLevel, getWeeklyMessage } from "../hooks/messages";
import { cn } from "../hooks/utils";
import { quests_types } from "../hooks/data"


// function Task(creds) {
//   const [message, setMessage] = useState('');
//   const [weeklyMessage, setWeeklyMessage] = useState('');
//   const [spointsLevel, setSpointsLevel] = useState('');
//   const [userData, setUserData] = useState({
//     spoints: 0,
//     xp: 0,
//     isDone: false
//   });

//   const onError = async (error) => {
//     console.error(error);
//     setMessage("Что-то пошло не так");
//   }

//   const submitTask = async () => {
//     const onCompleteTask = async (res) => {
//       if (res.data?.isUpLevel) {
//         setMessage(getMessageLevel());
//         setSpointsLevel(res.data.spointsLevel)
//       } else {
//         setMessage(getMessageTask());
//       }

//       if (res.data?.isWeekly) {
//         setWeeklyMessage(getWeeklyMessage());
//       }

//       // finally logics
//       setUserData({
//         spoints: res.data.points,
//         xp: res.data.xp,
//         isDone: true
//       });
//     }

//     await completeTask({
//       id: creds.id,
//       onCompleteTask: onCompleteTask,
//       onError: onError
//     })
//   }

//   const unSubmitTask = async () => {
//     const onUncompleteTask = async () => {
//       setMessage("Вы вернули задачу");
//       setSpointsLevel('')
//       setUserData({
//         spoints: 0,
//         xp: 0,
//         isDone: false
//       })
//     }

//     await uncompleteTask({
//       id: creds.id,
//       onUncompleteTask: onUncompleteTask,
//       onError: onError
//     })
//   }

//   const delTask = async () => {
//     const onDeleteTask = async (title) => {
//       setMessage(`Задача ${title} успешно удалена`);
//       setUserData(prev => ({
//         ...prev,
//         isDone: false
//       }))
//     }

//     await deleteTask({
//       id: creds.id,
//       onDeleteTask: onDeleteTask,
//       onError: onError
//     })
//   }

//   return (
//     <div>
//       <p className="font-bold text-lg">
//         {creds.index + 1}. {creds.title}
//       </p>
//       <p>
//         Тип задания: <b>{quests_types[creds.type]}</b>
//       </p>
//       {creds.description &&
//         <p className="mt-1 font-mono">{creds.description}</p>
//       }

//       {message && <p className="font-medium">{message}</p>}

//       <div className="space-y-1">
//         {userData.xp > 0 && userData.spoints > 0 &&
//           <>
//             <p>Награда: <b>+{userData.spoints} Spoints +{userData.xp} Xp</b> </p>
//           </>}
//         {spointsLevel && <p>Уровень повышен, награда: <b>+{spointsLevel} Spoints</b></p>}
//       </div>

//       {weeklyMessage && <p className="font-medium">{weeklyMessage}</p>}

//       {!userData.isDone ? (
//         <>
//           <button
//             className="block mt-2 bg-gray-200 px-1 rounded-md border border-gray-600"
//             onClick={submitTask}
//             type='button'>
//             Сделано
//           </button>
//           <button
//             className="block mt-2 bg-red-500 px-1 rounded-md border border-black"
//             onClick={delTask}
//             type='button'>
//             Удалить
//           </button>
//         </>
//       ) : (
//         <button
//           className="block mt-2 bg-gray-200 px-1 rounded-md border border-gray-600"
//           onClick={unSubmitTask}
//           type='button'>
//           Вернуть
//         </button>
//       )
//       }
//     </div>
//   )
// }

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
      unCompleteTask({
        id: creds.id
      })
    } else {
      setIsSubmit(true);
      completeTask({
        id: creds.id
      })
    }
  }

  const delTask = async() => {
    setTrashSrc("/task/trash_active.png");
    deleteTask({
      id: creds.id
    })
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
          showSubmit ? "opacity-100": "opacity-0 pointer-events-none"
        )}
        onMouseEnter={() => {setTrashSrc("/task/trash_hover.png")}}
        onMouseLeave={() => {setTrashSrc("/task/trash.png")}}
        onMouseDown={delTask}
        onMouseUp={() => {setTrashSrc("/task/trash_hover.png")}}>

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
              <Task key={_id} id={_id} title={title} description={description} />
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
                type={creds.type} />
            </div>
          ) : (
            <button
              className="mt-2 text-[#7C8AA0] p-1 pl-2 w-full rounded-md text-left cursor-pointer hover:bg-[#EEF2F7] active:bg-[#E5E9F0]"
              type="button"
              onClick={() => { setIsFormCreateTask(true)}}>
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

  useEffect(() => {
    const onFinish = data => {
      setTasks(data.tasks);
      setTypeTasks(data.type_tasks);
    }

    getTasks({ onFinish });
  }, []);

  console.log(typeTasks)
  return (
    <div className="flex items-start ml-2 mt-4 space-x-3">
      {typeTasks.map(type => (
        <CanbanDesk
          title={quests_types[type]}
          type={type}
          tasks={tasks} />
      ))}
      {/* <div className="space-y-4">
       {tasks.map((task, index) => (
          <Task
            key={task._id}
            id={task._id}
            index={index}
            title={task.title}
            description={task.description}
            type={task.type}
          />
        ))}
      </div> */}
    </div>
  );
};
