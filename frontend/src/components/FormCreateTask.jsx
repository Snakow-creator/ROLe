export default function FormCreateTask(creds) {
  return (
    <form onSubmit={() => {}}
          className="mt-2">
      <textarea type=""
        className="bg-white appearance-none resize-none border border-[#F1F1F1] w-full h-16 shadow outline-2 outline-blue-400 hover:outline-0 rounded-md text-left p-1 px-2"
        placeholder="Введите заголовок квеста"
        maxLength="100"/>
    </form>
  )
}
