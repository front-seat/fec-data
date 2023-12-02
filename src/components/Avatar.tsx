import clsx from "clsx";

/** Avatar with text interior, usually used for user initials */
export const TextAvatar: React.FC<
  React.PropsWithChildren<{ className?: string }>
> = ({ children, className }) => (
  <span
    className={clsx(
      "inline-flex items-center justify-center rounded-full",
      className
    )}
  >
    <span className="text-lg font-medium leading-none text-white">
      {children}
    </span>
  </span>
);

/** Avatar with image. */
export const ImageAvatar: React.FC<{
  src: string;
  alt: string;
  className?: string;
}> = ({ src, alt, className }) => (
  <img
    className={clsx("inline-block rounded-full", className)}
    src={src}
    alt={alt}
  />
);
