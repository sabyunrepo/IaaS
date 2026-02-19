/**
 * @file ui:skeleton
 * @requires @seed-design/react@~1.0.0
 * @requires @seed-design/css@~1.0.0
 **/

import { Skeleton as SeedSkeleton, type SkeletonProps as SeedSkeletonProps } from "@seed-design/react"
import * as React from "react"

export interface SkeletonProps extends SeedSkeletonProps {}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>((props, ref) => {
  return <SeedSkeleton ref={ref} {...props} />
})
Skeleton.displayName = "Skeleton"
