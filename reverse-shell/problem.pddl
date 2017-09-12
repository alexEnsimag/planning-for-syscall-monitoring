(define (problem detect-remote-shell)
	(:domain remote-shell)
	(:objects
			fd3 - fd
			fd4 - fd
			sh - path
	)
	(:init
            (opened fd0)
            (opened fd1)
            (opened fd2)
            (is-shell sh)
	)

	(:goal  (exists (?sh - path) (remote-shell-started ?sh)))
)
