/**
 * @file ui:divider
 * @requires @seed-design/react@~1.0.0
 * @requires @seed-design/css@~1.0.0
 **/

import { Divider as SeedDivider, type DividerProps as SeedDividerProps } from "@seed-design/react"
import * as React from "react"

export interface DividerProps extends SeedDividerProps {}

export const Divider = React.forwardRef<HTMLHRElement, DividerProps>((props, ref) => {
  return <SeedDivider ref={ref} {...props} />
})
Divider.displayName = "Divider"
