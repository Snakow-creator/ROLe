

export default function(creds) {
  return (
    <div className="flex items-center space-x-1">
      <p className="font-medium text-lg">
        {creds.title}
      </p>
      <b className="font-extrabold text-lg text-black">
        {creds.children}
      </b>
    </div>
  )
}
