export default function Spinner() {
  return (
    <>
    <div className="fixed z-40 h-screen w-screen flex justify-center items-center">
    </div>
    <div className="absolute top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 z-50 loader" ></div>
    </>
  )
};
