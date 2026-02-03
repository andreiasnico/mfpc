# MFPC Exam — 50 Multiple-Choice Questions (A–D)

In a labelled transition system (LTS), a transition is a triple (s, a, s'). What does "a" represent?  
A. state label  
B. action/label  
C. initial state  
D. final state  
Answer: B

In CCS, the prefix operator a.P means:  
A. P executes, then a  
B. action a then behave like P  
C. nondeterministic choice between a and P  
D. parallel composition of a and P  
Answer: B

The CCS choice operator P + Q represents:  
A. nondeterministic choice  
B. sequencing of P then Q  
C. parallel composition  
D. hiding of actions  
Answer: A

Which CCS operator restricts (hides) a set of actions from the environment?  
A. |  
B. .  
C. \ (backslash / restriction)  
D. +  
Answer: C

Strong bisimulation requires that:  
A. traces are identical  
B. actions match including internal steps  
C. only observable actions match (τ ignored)  
D. states counts are equal  
Answer: B

Weak bisimulation differs from strong bisimulation by:  
A. ignoring internal τ steps  
B. requiring deterministic processes  
C. matching only first actions  
D. disallowing recursion  
Answer: A

Two processes are trace-equivalent if:  
A. they have same branching structure  
B. they can perform the same sets of action sequences  
C. they are bisimilar  
D. they share the same states  
Answer: B

A deadlock is:  
A. livelock with infinite τ  
B. a state with no outgoing transitions for involved processes  
C. one process blocked, others continue  
D. a state with only τ transitions  
Answer: B

Livelock is best described as:  
A. permanent blocked state  
B. infinite internal activity preventing progress  
C. two processes both waiting on each other  
D. a successful termination  
Answer: B

Structural operational semantics (SOS) specify:  
A. code generation rules  
B. transition rules defining process behaviour  
C. performance metrics  
D. memory layout  
Answer: B

In parallel composition P | Q, synchronization on complementary actions typically produces:  
A. choice  
B. τ (internal) action  
C. deadlock always  
D. renaming  
Answer: B

The CCS relabelling operator is used to:  
A. hide actions  
B. rename labels for synchronization  
C. duplicate actions  
D. eliminate recursion  
Answer: B

Recursive process definitions in CCS allow:  
A. finite-state only  
B. infinite behaviour via recursion  
C. only deterministic behaviour  
D. hiding of names only  
Answer: B

Congruence property for an equivalence relation means:  
A. equivalence preserved in any process context  
B. same number of states  
C. same set of actions  
D. identical syntax  
Answer: A

Bisimulation up-to techniques are used to:  
A. enumerate all states  
B. simplify bisimulation proofs by allowing approximations  
C. convert CCS to Petri nets  
D. check trace equivalence  
Answer: B

In process algebra, the law P + P = P expresses:  
A. associativity  
B. idempotence of choice  
C. commutativity  
D. distributivity  
Answer: B

Label hiding (restriction) often changes:  
A. the set of visible actions  
B. number of processes  
C. variable types  
D. recursion depth  
Answer: A

A labelled transition system node with no outgoing observable actions but with τ-loops is:  
A. deadlock  
B. livelock  
C. bisimilar to termination  
D. deterministic  
Answer: B

Model checking typically verifies:  
A. code style  
B. reachability and temporal properties  
C. memory leaks  
D. runtime speed  
Answer: B

In CCS, synchronous communication requires:  
A. buffering channels  
B. both sender and receiver to be ready  
C. a scheduler only  
D. global variables  
Answer: B

In a programming context, atomicity means:  
A. unlimited parallelism  
B. operation appears indivisible  
C. requires locking always  
D. deterministic scheduling  
Answer: B

Semaphore.acquire() in threading blocks when:  
A. value > 0  
B. value == 0  
C. always  
D. never  
Answer: B

Semaphore.release() typically:  
A. decrements counter  
B. increments counter and wakes waiters  
C. sets daemon flag  
D. cancels threads  
Answer: B

BoundedSemaphore differs from Semaphore by:  
A. allowing negative value  
B. having an upper bound on the counter  
C. being non-blocking only  
D. using reentrancy  
Answer: B

Lock.acquire(blocking=True) returns:  
A. None  
B. True on success, False if non-blocking and failed  
C. raises exception always  
D. thread id  
Answer: B

RLock (reentrant lock) allows:  
A. same thread to acquire multiple times  
B. only one acquisition ever  
C. unlocking by different thread  
D. no locking semantics  
Answer: A

Condition.wait() must be called:  
A. without holding associated lock  
B. while holding the associated lock  
C. only by main thread  
D. after notify only  
Answer: B

Condition.notify() wakes:  
A. all waiting threads always  
B. one or n waiting threads  
C. only the thread that called wait  
D. no threads  
Answer: B

Event.set() causes Event.wait() to:  
A. block  
B. return immediately for subsequent waiters  
C. raise BrokenBarrierError  
D. timeout  
Answer: B

Timer.cancel() will:  
A. start the timer  
B. prevent the timer's function from running if not yet started  
C. block until timer fires  
D. reset the interval  
Answer: B

Barrier.wait() returns an index that:  
A. is always zero  
B. indicates which thread is the "leader"  
C. is a thread id  
D. signals timeout  
Answer: B

BrokenBarrierError is raised when:  
A. barrier parties < 2  
B. barrier is aborted or broken during wait  
C. barrier finishes normally  
D. no threads use the barrier  
Answer: B

Thread.start() must be called:  
A. before creating the Thread object  
B. once to start thread execution  
C. multiple times allowed  
D. only by daemon threads  
Answer: B

Thread.join(timeout) does:  
A. forcibly kills thread  
B. waits until thread terminates or timeout elapses  
C. detaches thread from process  
D. raises BrokenBarrierError  
Answer: B

Thread.daemon = True means:  
A. thread will prevent process exit  
B. thread won't keep Python process alive  
C. thread is paused  
D. thread is a timer  
Answer: B

Thread.ident is:  
A. the native OS thread id always  
B. a unique identifier for the thread object or None if not started  
C. the thread name  
D. thread priority  
Answer: B

Event.wait(timeout=None) returns:  
A. True if the event is set, False on timeout  
B. raises exception  
C. returns thread id  
D. always None  
Answer: A

Semaphore.enter allows usage of:  
A. with statement for acquire/release  
B. only manual acquire/release  
C. context managers for threads only  
D. creating a new semaphore  
Answer: A

RLock.locked() (if available) indicates:  
A. if any thread holds the lock  
B. whether current thread holds it  
C. number of holders  
D. timeout remaining  
Answer: A

In CCS, restriction of a synchronizing action on P|Q that would synchronize can lead to:  
A. a visible handshake instead of τ  
B. deadlock because synchronization cannot occur  
C. duplication of actions  
D. automatic renaming  
Answer: B

Trace equivalence is weaker than bisimulation because:  
A. it considers branching structure  
B. it ignores branching and internal structure  
C. it requires matching τ transitions  
D. it enforces congruence  
Answer: B

If two processes are strongly bisimilar, then they are:  
A. trace-equivalent  
B. always syntactically identical  
C. necessarily deterministic  
D. unreachable  
Answer: A

The main_thread() function returns:  
A. the current thread  
B. the initial thread that started the program  
C. a new Thread object  
D. None  
Answer: B

settrace() in threading sets:  
A. global interpreter lock  
B. a trace function for new threads  
C. scheduling policy  
D. thread name  
Answer: B

TIMEOUT_MAX is:  
A. maximum allowable timeout value used by threading APIs  
B. number of threads allowed  
C. size of thread stack  
D. minimum timeout  
Answer: A

In process algebra, an action prefix followed by recursion typically models:  
A. finite loop only  
B. infinite repetitive behaviour  
C. immediate termination  
D. concurrency only  
Answer: B

A semantic rule in SOS of the form (a.P) -a-> P is an example of:  
A. structural law  
B. prefix rule (transition axiom)  
C. restriction rule  
D. parallel rule  
Answer: B

A scheduler implementing interleaving semantics assumes:  
A. true simultaneous execution of instructions  
B. atomic steps interleaved nondeterministically  
C. actions are synchronized by default  
D. no context switches  
Answer: B

In testing for weak bisimulation, τ-transitions are:  
A. matched exactly  
B. collapsed/abstracted over in matches  
C. forbidden  
D. renamed to visible actions  
Answer: B

A Condition.notify_all() is equivalent to:  
A. notifying one waiter  
B. waking all threads waiting on the condition  
C. setting an Event  
D. releasing the lock  
Answer: B