package register

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/smart-inner/smarttune/util/http"
	"github.com/spf13/cobra"
	"os"
	"strings"
)

type RegisterOptions struct {
	Backend string

	genericclioptions.IOStreams
}

func NewRegisterOptions(streams genericclioptions.IOStreams) *RegisterOptions {
	return &RegisterOptions{
		IOStreams: streams,
	}
}

func NewCmdRegister(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewRegisterOptions(streams)
	cmd := &cobra.Command{
		Use:   "register SYSTEM --backend=backend",
		Short: "Register system catalog, such as tidb@v6.1.0, mysql@v5.7.0",
		Long:  `Register system catalog, which include system type and version, knobs and metrics catalog`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Register(args))
		},
	}
	addRegisterFlags(cmd, o)

	return cmd
}

func addRegisterFlags(cmd *cobra.Command, opt *RegisterOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "",
		"The backend <ip:port> for smarttune server, such as '127.0.0.1:5000'")
}

func (o *RegisterOptions) RegisterSystem(url, file string) (string, error) {
	content, err := os.ReadFile(file)
	request := make(map[string]interface{})
	if err = json.Unmarshal(content, &request); err != nil {
		return "", err
	}
	resp, err := http.PostJSON(url, request)
	if err != nil {
		return "", err
	}
	return http.HandleResponse(resp)
}

func (o *RegisterOptions) Register(args []string) error {
	if len(args) != 1 || len(o.Backend) == 0 {
		return errors.New(fmt.Sprintf("Error: invalid subcommand "+
			"'smartctl register %s --backend=%s'", strings.Join(args, " "), o.Backend))
	}
	smartTuneHome, err := util.GetHome()
	if err != nil {
		return err
	}
	supportedSystem, err := util.GetSupportedSystem(fmt.Sprintf("%s/resource/templates", smartTuneHome))
	if err != nil {
		return err
	}
	if util.Contain(supportedSystem, strings.ToLower(args[0])) {
		url := fmt.Sprintf("http://%s/api/system/register", o.Backend)
		requestFile := fmt.Sprintf("%s/resource/templates/%s/system.json",
			smartTuneHome, strings.ToLower(args[0]))
		out, err := o.RegisterSystem(url, requestFile)
		if err != nil {
			return err
		}
		fmt.Fprintf(o.Out, out)
	} else {
		return errors.New(fmt.Sprintf("Error: unable to register '%s', "+
			"the list of supported systems is [%s]", args[0], strings.Join(supportedSystem, ", ")))
	}

	return nil
}
