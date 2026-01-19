import { useRef, useEffect } from "react"

import { cn } from "../hooks/utils";

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

  const ref = useAutoResizeTextArea({focus: creds.focus, value: creds.value});

  return (
    <textarea
    ref={ref}
    rows="1"
    onChange={creds.onChange}
    name={creds.name}
    value={creds.value}
    placeholder={creds.placeholder}
    className={creds.className}
    maxLength={creds.maxLength}>
    </textarea>
  )
}
