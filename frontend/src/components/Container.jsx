export default function Container(creds) {
  return (
    <div className='mt-2 lg:w-[70%] md:w-[80%] sm-[90%] mx-auto text-center'>
      {creds.children}
    </div>
  )
}
