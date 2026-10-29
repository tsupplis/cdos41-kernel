# System generation

GENCCPM 4.1 has been built from GENC1..6.C in commands/genccpm.
The selected components build in kernel/con and kernel/rsp1..3.
The final image must retain the name CCPM.SYS expected by GENCCPM/loaders.

A validated 4.1 response file and isolated component staging Makefile are
still required. Do not reuse the 3.1 response file blindly: the 4.1
hashing/buffer questions differ and misalign the subsequent answers.
Boot media are a later step; no incomplete system image is a build output.
