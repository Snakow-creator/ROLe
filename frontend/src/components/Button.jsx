import { cn } from "../hooks/utils";

export default function Button (props) {
  return (
    <button
      className={cn(
        "block px-1 cursor-pointer rounded-md bg-[#3B82F6] text-white hover:bg-[#2563EB] active:bg-[#1D4ED8] border border-[#2563EB]",
        props.isDone && "block mt-4 px-1 mx-auto cursor-pointer rounded-md bg-[#86EFAC] text-[#1E293B] hover:bg-[#4ADE80] active:bg-[#22C55E] border border-[#4ADE80]",
        props.className,
      )}
      onClick={props.onClick}
      type={props.type}>
      {props.children}
    </button>
  );
}
