import { useEffect } from "react";

export function useOutsideClick(ref, isActive, onOutside) {
  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        onOutside();
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => {
      document.removeEventListener("mousedown", handleClick)
    }
  }, [ref, isActive, onOutside])
}
