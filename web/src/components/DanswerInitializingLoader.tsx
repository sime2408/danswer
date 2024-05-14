import { Bold } from "@tremor/react";
import Image from "next/image";
import {useTheme} from "@/app/ThemeContext";

export function DanswerInitializingLoader() {

  const { theme } = useTheme();
  const logoSrc = theme === 'dark' ? '/logo-dark.png' : '/logo.png';

  return (
    <div className="mx-auto animate-pulse">
      <div className="h-24 w-24 mx-auto mb-3">
        <Image src={logoSrc} alt="Logo" width="1419" height="1520" />
      </div>
      <Bold>Initializing Adcubum</Bold>
    </div>
  );
}
