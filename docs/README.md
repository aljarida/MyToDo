# Philosophy

MyToDo is made with specific philosophies in mind:
- Adding, deleting, and completing tasks should be **instantaneous**.
- As **little hand movement** as possible should be needed; thoughts should move to storage without friction.
- The MyToDo application should be **accessible anywhere, ASAP**.
- Complexity should be low.

These philosophies make MyToDo great for jotting down spontaneous thoughts that may arise while working or in flow that might typically create much distraction and waiting as Notion, Todoist, or even Microsoft Word slowly whir awake. 

MyToDo encourages you to discard tasks you are not able complete in the short- or medium-term. The limited space of a CLI lends itself to having a smaller set of tasks on your plate, and this restriction enables you to think critically about which tasks are relevant to your present self and which may be too vague, long-term, or high-level. MyToDo is a vehicle for accomplishing real tasks quickly. It takes you from writing "Become a great developer" to "Complete the first lecture video for Missing Semester".

The bread and butter of MyToDo are three commands: List, complete, delete. Its workflow is super simple and easy to get into. `mtd -l` and `mtd -c` have been designed to feel just like using `ls` and `cd` in Bash. Those comfortable with CLIs will feel right at home here.

## Core Workflow

### 1. Add a Task
```powershell
$ mtd -a "Complete the MyToDo tutorial"
Added task "Complete the MyToDo tutorial".
$ mtd -a "Relearn Emacs and GTD philosophy"
Added task "Relearn Emacs and GTD philosophy".
```

Tasks are added using the `-a` flag. Use quotation marks `"` or `'` to delimit the task.


### 2. List Tasks
```powershell
$ mtd -l
1. Complete the MyToDo tutorial
2. Relearn Emacs and GTD philosophy 
3. Figure out where these extra tasks came from
4. Complain on Twitter about Spirit Airlines
5. Feel accomplished
```


### 3. Delete Tasks
```poweshell
$ mtd -d 2 3 4 
Deleted task "Figure out where these extra tasks came from"
Deleted task "Relearn Emacs and GTD philosophy".
Deleted task "Complain on Twitter about Spirit Airlines"
```

```powershell
$ mtd -l
1. Complete the MyToDo tutorial
2. Feel accomplished
```

### 4. Complete Tasks
```powershell
$ mtd -c 1 2
Completed task "Complete the MyToDo tutorial"
Completed task "Feel accomplished"
```

```powershell
$ mtd -l
No tasks to show.
```

### Tips and Tricks
* Use negative indices to complete or delete tasks just like Python's native negative indexing for lists. `mtd -d -1` will delete the most recent task added, for example.
* Use `-h` to display help. This is particularly helpful for finding the longer flags such as `--list` for `-l`. Some may find the longer flags useful for initial learning.
* Use the `-v` flag to get verbose information on the underlying task data including time of creation and time of completion.
* Use `mtd -up idx 0` (where `idx` is the task index) to remove priority from a task.
