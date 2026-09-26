# Asteriq economy production guard

The default target is one euro per final output minute after the model cache is
warm. It is a cap policy, not a promise that every source can receive a full
diffusion re-render within that amount.

## Concept frames

Use the cached Segmind SSD-1B model for text-to-image concept frames and
character/set design sheets. It is kept separate from the long-video budget so
creative direction can be approved before expensive animation work begins.

## Economy route

1. Make a low-resolution local proxy and retain the original timebase.
2. Track each manually assigned performer once; reuse tracks across retries.
3. Retarget motion onto the saved, versioned character rig.
4. Render the reusable virtual set, camera, lighting, wardrobe and props with
   the deterministic renderer.
5. Batch each character's dialogue through its saved voice profile.
6. Apply a generative look pass only to approved shots that fit the remaining
   runtime budget.
7. Assemble the one-minute episode from checkpointed shots. A 4K finish is a
   separate costed task.

The worker must stop or downgrade remaining optional look passes before its
per-minute GPU runtime ceiling. It must never restart a full episode because a
single shot failed.
