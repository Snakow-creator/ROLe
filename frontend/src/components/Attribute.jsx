

export default function Attribute({title, children}) {
  return (
    <div className="flex items-center space-x-1">
      <p className="font-medium text-lg">
        {title}
      </p>
      <p className="font-extrabold text-lg text-black">
        {children}
      </p>
    </div>
  )
}
