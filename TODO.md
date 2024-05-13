- service yml
  - [ ] auto task discovery

- Tests
  - [x] ServiceManager
  - [ ] EntityManager

# Features
- [ ] Async
  - [ ] Client
  - [ ] Server
  - [ ] Task Code
- [ ] Composites: workflows on the fly with a simple DSL for result composition.
- [ ] Datagen (Entities, service folders, task folders - all yml files, etc)
- [ ] Project
- [ ] Definable Entity and Service Actions (like Tasks)
## Maybe
- discover all workflows for client 
- allow ctx return from task? (semi-bug - circular ref if return ctx)
- entity yml
  - [ ] broadcast subservice to main controller. "fake common service"
  - [ ] save workflow or composite results to file for later use - project?
  - [ ] service: Literal['all', 'mine'] | list[str]
- [ ] service yml
  - [ ] auto task discovery - tasks: Literal['all'] | list[str]

- task yaml?
  - maybe we define task just like entity and service, and have it find a raw function in python, or add the code to the yaml file.

- run() wrapper to make workflow and contexts transparent to task code
- [ ] client and server folders? gettin phat.
# BUGS
- Annoyingly, only dizae server/client logs right now. For  some reason logfiles don't work at the right levels either.

