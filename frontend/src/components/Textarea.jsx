import { useRef, useEffect, use } from "react"

function useAutoResizeTextArea(creds) {
  const ref = useRef(null);

  useEffect(() => {
    if (creds.focus) {
      ref.current?.focus();
    }
  }, [])

  useEffect(() => {
    const el = ref.current

    if (el) {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }
  }, [creds.value]);

  return ref
}

export default function Textarea (creds) {

  const ref = useAutoResizeTextArea({focus: creds.focus, name: creds.name});

  return (
    <textarea
      ref={ref}
      rows="1"
      onChange={creds.onChange}
      name={creds.name}
      placeholder={creds.placeholder}
      maxLength={creds.maxLength}
      className={creds.className}>
    </textarea>
  )
}
