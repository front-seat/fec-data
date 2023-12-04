export const Hero: React.FC<{ onGetStarted: () => void }> = ({
  onGetStarted,
}) => (
  <>
    <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
      Team up against{" "}
      <span className="text-red-600 line-through">Trump&nbsp;</span>
    </h1>
    <p className="mt-6 text-xl sm:text-2xl leading-8 sm:leading-10 text-gray-600">
      Can you raise more than <strong>$250</strong>? Then <strong>TxT</strong>{" "}
      is the <strong>most effective</strong> way to make sure Trump never sees
      the White House again.
    </p>
    <div className="mt-10 flex items-center justify-center gap-x-6">
      <a
        href="#"
        onClick={onGetStarted}
        className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-lg font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
      >
        Get started
      </a>
      <a href="#" className="text-lg font-semibold leading-6 text-gray-900">
        Learn more <span aria-hidden="true">→</span>
      </a>
    </div>
  </>
);
