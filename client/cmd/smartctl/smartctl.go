package main

import (
	"github.com/smart-inner/smarttune/pkg/cli"
	"github.com/smart-inner/smarttune/pkg/smartctl/cmd"
	"github.com/smart-inner/smarttune/util"
)

func main() {
	command := cmd.NewDefaultSmartctlCommand()
	if err := cli.RunNoErrOutput(command); err != nil {
		util.CheckErr(err)
	}
}
