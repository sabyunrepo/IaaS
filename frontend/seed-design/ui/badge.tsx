/**
 * @file ui:badge
 * @requires @seed-design/react@~1.0.0
 * @requires @seed-design/css@~1.0.0
 **/

import { Badge as SeedBadge, type BadgeProps as SeedBadgeProps } from "@seed-design/react"
import * as React from "react"

export interface BadgeProps extends SeedBadgeProps {}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>((props, ref) => {
  return <SeedBadge ref={ref} {...props} />
})
Badge.displayName = "Badge"
