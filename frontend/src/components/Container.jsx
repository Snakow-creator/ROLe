export default function Container({ children }) {
  return (
    <div className='mt-2 w-full lg:w-[70%] md:w-[80%] sm:w-[90%] mx-auto text-center'>
      {children}
    </div>
  )
}
