interface IImageLoadingProps {
  spinningRadius?: number;
}

export default function ImageLoading({
  spinningRadius = 40,
  ...props
}: React.SVGProps<SVGSVGElement> & IImageLoadingProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" {...props}>
      <radialGradient
        id="a11"
        cx=".66"
        fx=".66"
        cy=".3125"
        fy=".3125"
        gradientTransform="scale(1.5)"
      >
        <stop offset="0" stopColor="#000091"></stop>
        <stop offset=".3" stopColor="#000091" stopOpacity=".9"></stop>
        <stop offset=".6" stopColor="#000091" stopOpacity=".6"></stop>
        <stop offset=".8" stopColor="#000091" stopOpacity=".3"></stop>
        <stop offset="1" stopColor="#000091" stopOpacity="0"></stop>
      </radialGradient>
      <circle
        transform-origin="center"
        fill="none"
        stroke="url(#a11)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray="200 1000"
        strokeDashoffset="0"
        cx="100"
        cy="100"
        r={`${spinningRadius}`}
      >
        <animateTransform
          type="rotate"
          attributeName="transform"
          calcMode="spline"
          dur="1.1"
          values="360;0"
          keyTimes="0;1"
          keySplines="0 0 1 1"
          repeatCount="indefinite"
        ></animateTransform>
      </circle>
      <circle
        transform-origin="center"
        fill="none"
        opacity=".2"
        stroke="#000091"
        strokeWidth="2"
        strokeLinecap="round"
        cx="100"
        cy="100"
        r={`${spinningRadius}`}
      ></circle>
    </svg>
  );
}
