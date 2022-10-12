package util

import (
	"errors"
	"fmt"
	errorsutil "github.com/smart-inner/smarttune/util/errors"
	"os"
	"strings"
)

const (
	// DefaultErrorExitCode defines exit the code for failed action generally
	DefaultErrorExitCode = 1
	// ValidationExitCode defines the exit code validation checks
	ValidationExitCode = 2
)

var (
	ErrInvalidSubCommandMsg = "invalid subcommand"
	ErrExit                 = errors.New("exit")
)

// fatal prints the message if set and then exits.
func fatal(msg string, code int) {
	if len(msg) > 0 {
		// add newline if needed
		if !strings.HasSuffix(msg, "\n") {
			msg += "\n"
		}

		fmt.Fprint(os.Stderr, msg)
	}
	os.Exit(code)
}

// CheckErr prints a user-friendly error to STDERR and exits with a non-zero
// exit code. Unrecognized errors will be printed with an "error: " prefix.
func CheckErr(err error) {
	checkErr(err, fatal)
}

// checkErr formats a given error as a string and calls the passed handleErr
// func with that string and an exit code.
func checkErr(err error, handleErr func(string, int)) {
	if err == nil {
		return
	}
	switch {
	case err == ErrExit:
		handleErr("", DefaultErrorExitCode)
	case strings.Contains(err.Error(), ErrInvalidSubCommandMsg):
		handleErr(err.Error(), DefaultErrorExitCode)
	default:
		switch err.(type) {
		case errorsutil.Aggregate:
			handleErr(err.Error(), ValidationExitCode)
		default:
			handleErr(err.Error(), DefaultErrorExitCode)
		}
	}
}
