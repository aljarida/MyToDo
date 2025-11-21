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

## Advanced Usage

### View Completed Tasks
You can list completed tasks using the `-lc` flag. By default, the most recent 5 tasks are listed.
```
mtd -lc
```

You can specify the `n` most recent or `n` oldest via `mtd -lc n` or `mtd -lc -n` where `n` is an integer.
```powershell
$ mtd -lc -15
```

You also list all completed tasks by adding the `-sa` flag.
```
mtd -lc -sa
```

### View Log
View the log of prior actions by using the `-vl` flag. The five most recent actions will display. 

```
mtd -vl
```

To see all actions ever, add the `-sa` flag.

```
mtd -vl -sa
```

### Set Priorities

You can set a priority when creating a task.
```powershell
$ mtd -a "Uninstall Todoist" -p 3
Added task "Uninstall Todoist".
```

```powershell
$ mtd -l
1. *P3* Uninstall Todoist
```

Alternatively, you can update a task's priority using `-up idx n` whre `idx` is the task index and `n` is the new priority.

```powershell
$ mtd -sp 1 4
Set priority of "Uninstall Todoist" to 4.
```

Priorities range from `0` to `4`.
- `0` is a special number indicating lack of priority.
- `1` is the first real priority and the lowest rank of prioritization.
- `4` is the greatest priority. 

### Priority Sort
Say you have a list like the following:
```powershell
$ mtd -l
1. *P2* Eat
2. *P3* Drink
3. Shelter
4. *P4* Reproduce
5. *P1* Socialize
```

You can sort it by priority using the `-ps` flag.
```powershell
$ mtd -l -ps 
4. *P4* Reproduce
2. *P3* Drink
1. *P2* Eat
5. *P1* Socialize
3. Shelter
```

### Tips and Tricks
* Use negative indices to complete or delete tasks just like Python's native negative indexing for lists. `mtd -d -1` will delete the most recent task added, for example.
* Use `-h` to display help. This is particularly helpful for finding the longer flags such as `--list` for `-l`. Some may find the longer flags useful for initial learning.
* Use the `-v` flag to get verbose information on the underlying task data including time of creation and time of completion.
* Use `mtd -up idx 0` (where `idx` is the task index) to remove priority from a task.

