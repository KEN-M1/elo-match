"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";

import { syncSessionActor } from "../../lib/actor";

export function SessionSync() {
  const { data: session } = useSession();

  useEffect(() => {
    syncSessionActor(session ?? {}).catch(() => {
      // The local demo flow can still work without backend session sync.
    });
  }, [session]);

  return null;
}
