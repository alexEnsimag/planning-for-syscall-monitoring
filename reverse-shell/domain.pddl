(define (domain remote-shell)
    (:requirements :adl)

    (:types
        fd ; file descriptor (file or socket)
        path
        boolean
        command
    )

    (:constants fd0 - fd
                fd1 - fd
                fd2 - fd
                NULL - fd
                True - boolean
                False - boolean
                F_DUPFD - command
                F_SETFD - command
                F_DUPFD_CLOEXEC - command
    )
    
    (:predicates
        ;; file descriptor
        (opened ?fd - fd)
        (is-socket ?fd - fd)
        (connected ?fd - fd)
        (equal-fds ?fd1 - fd ?fd2 - fd)
        (close-on-exec ?fd - fd)

        ;; file tainting
        (is-shell ?path - path)

        ;; behavior
        (remote-shell-started ?path - path)
    ) 

    (:action socket
        :parameters     (?returned-fd - fd ?cloexec - boolean)
        :precondition   ()
        :effect         (and    (when   (not    (opened ?returned-fd))
                                        (and    (opened ?returned-fd)
                                                (is-socket ?returned-fd)))
                                (when   (and    (not (opened ?returned-fd))
                                                (= ?cloexec True))
                                        (close-on-exec ?returned-fd))
                        )
    )

    (:action connect
        :parameters     (?fd - fd)
        :precondition   ()
        :effect         (and    (when   (and    (opened ?fd)
                                            (is-socket ?fd)
                                            (not (connected ?fd)))
                                    (connected ?fd))
                                (forall (?fd2 - fd) ; when already duplicated
                                        (when   (and    (opened ?fd)
                                                        (is-socket ?fd)
                                                        (not (connected ?fd))
                                                        (equal-fds ?fd ?fd2))
                                                (connected ?fd2))
                                )
                        )  
    )

    (:action dup
        :parameters     (?fd - fd ?returned-fd - fd)
        :precondition   ()
        :effect         (and    (when       (and    (opened ?fd) 
                                                    (not (opened ?returned-fd)))
                                            (and    (opened ?returned-fd) 
                                                    (equal-fds ?fd ?returned-fd)
                                                    (equal-fds ?returned-fd ?fd)))
                                (when       (and    (is-socket ?fd)
                                                    (opened ?fd) 
                                                    (not (opened ?returned-fd))) 
                                            (is-socket ?returned-fd))
                                (when       (and    (connected ?fd)
                                                    (opened ?fd) 
                                                    (not (opened ?returned-fd))) 
                                            (connected ?returned-fd))   
                                (forall (?fd2 - fd) ; when already duplicated
                                        (when   (and    (equal-fds ?fd ?fd2)
                                                        (not (opened ?returned-fd)))
                                                (and    (equal-fds ?fd2 ?returned-fd)
                                                        (equal-fds ?returned-fd ?fd2)))
                                )                
                            )
    )

    (:action fcntl
        :parameters     (?fd - fd ?cmd - command ?returned-fd - fd ?cloexec - boolean)
        :precondition   ()
        :effect         (and        (when       (and    (or (= ?cmd F_DUPFD) (= ?cmd F_DUPFD_CLOEXEC))
                                                        (opened ?fd) 
                                                        (not (opened ?returned-fd)))
                                                (and    (opened ?returned-fd) 
                                                        (equal-fds ?fd ?returned-fd)
                                                        (equal-fds ?returned-fd ?fd)))
                                    (when       (and    (or (= ?cmd F_DUPFD) (= ?cmd F_DUPFD_CLOEXEC))
                                                        (is-socket ?fd)
                                                        (opened ?fd) 
                                                        (not (opened ?returned-fd))) 
                                                (is-socket ?returned-fd))
                                    (when       (and    (or (= ?cmd F_DUPFD) (= ?cmd F_DUPFD_CLOEXEC))
                                                        (connected ?fd)
                                                        (opened ?fd) 
                                                        (not (opened ?returned-fd))) 
                                                (connected ?returned-fd))   
                                    (forall (?fd2 - fd) ; when already duplicated
                                            (when   (and    (or (= ?cmd F_DUPFD) (= ?cmd F_DUPFD_CLOEXEC))
                                                            (equal-fds ?fd ?fd2)
                                                            (not (opened ?returned-fd)))
                                                    (and    (equal-fds ?fd2 ?returned-fd)
                                                            (equal-fds ?returned-fd ?fd2)))
                                    )
                                    (when       (and    (or (and (= ?cmd F_SETFD) (= ?cloexec True))
                                                            (= ?cmd F_DUPFD_CLOEXEC))
                                                        (opened ?fd)
                                                        (not (opened ?returned-fd)))
                                                (close-on-exec ?returned-fd))
                                    (when       (and    (= ?cmd F_SETFD)
                                                        (= ?cloexec False)
                                                        (opened ?fd)
                                                        (not (opened ?returned-fd)))
                                                (not (close-on-exec ?returned-fd)))                      
                            )
    )

    (:action close
        :parameters     (?fd - fd)
        :precondition   ()
        :effect         (and    (not (opened ?fd))
                                (not (is-socket ?fd)) 
                                (not (connected ?fd))
                                (not (close-on-exec ?fd))
                                (forall (?fd2 - fd) 
                                    (when   (equal-fds ?fd ?fd2)
                                            (and    (not (equal-fds ?fd ?fd2))
                                                    (not (equal-fds ?fd2 ?fd))))
                                )
                        )
    )

    (:action execve 
       :parameters      (?path - path)
       :precondition    ()
       :effect          (when (and  (is-shell ?path)
                                    (exists (?fd - fd) 
                                        (and    (connected ?fd)
                                                (not (close-on-exec ?fd))
                                                (or (= ?fd fd0) (equal-fds ?fd fd0))
                                                (or (= ?fd fd1) (equal-fds ?fd fd1))
                                        )
                                    )
                               )
                               (remote-shell-started ?path)
                        )
    )
)